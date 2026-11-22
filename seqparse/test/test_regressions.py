"""Regression tests for bugs fixed in the seqparse library.

Each test pins down one previously broken behaviour. Filesystem-related tests
use real temporary directories (not mocked scandir) since symlinks, permissions
and path handling are exactly what the mocks could not exercise.
"""

import os
import tempfile
import unittest

from .. import get_parser, get_sequence, validate_frame_sequence
from ..cli import seqls
from ..containers import (
    FileExtension,
    FileSequenceContainer,
    SingletonContainer,
)
from ..sequences import (
    FileSequence,
    FrameSequence,
    SeqparsePadError,
)


class _TempDirMixin:
    """Provide a temporary directory and a helper for creating files."""

    def setUp(self):
        """Create the temporary directory."""
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name

    def make_files(self, *names, content=""):
        """Create (empty by default) files relative to the temp directory."""
        for name in names:
            path = os.path.join(self.root, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)

    def scan(self, path=None, stat=False, **kwargs):
        """Scan a path and return the string output of the parser."""
        parser = get_parser()
        parser.scan_options["stat"] = stat
        parser.scan_path(self.root if path is None else path, **kwargs)
        return parser

    def rel(self, items):
        """Strip the temp directory prefix from parser output."""
        return [os.path.relpath(str(x), self.root) for x in items]


###############################################################################
# Directory scanning


class TestScanning(_TempDirMixin, unittest.TestCase):
    """Regressions in Seqparse.scan_path and directory walking."""

    def setUp(self):
        """Create a three-level directory tree with one sequence per level."""
        super().setUp()
        self.make_files(
            "top.0001.exr",
            "a/mid.0001.exr",
            "a/b/low.0001.exr",
        )

    def test_list_of_paths_forwards_depth_limits(self):
        """scan_path([...]) used to ignore max_levels/min_levels."""
        parser = self.scan([self.root], max_levels=0)
        self.assertEqual(self.rel(parser.output()), ["top.0001.exr"])

        parser = self.scan([self.root], min_levels=2)
        self.assertEqual(self.rel(parser.output()), ["a/b/low.0001.exr"])

    def test_min_levels_matches_find_semantics(self):
        """min_levels was off by one (0 skipped the start dir, 1 skipped 1)."""
        everything = ["top.0001.exr", "a/mid.0001.exr", "a/b/low.0001.exr"]
        self.assertCountEqual(
            self.rel(self.scan(min_levels=0).output()), everything
        )
        self.assertCountEqual(
            self.rel(self.scan(min_levels=1).output()),
            ["a/mid.0001.exr", "a/b/low.0001.exr"],
        )

    def test_trailing_separator_does_not_shift_depth(self):
        """A trailing slash on the search path used to shift every level."""
        parser = self.scan(self.root + os.sep, max_levels=0)
        self.assertEqual(self.rel(parser.output()), ["top.0001.exr"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unsupported")
    def test_symlink_loop_terminates(self):
        """A symlink pointing at an ancestor recursed until OSError."""
        os.symlink(self.root, os.path.join(self.root, "a", "loop"))
        parser = self.scan()
        self.assertEqual(len(list(parser.output())), 3)

    @unittest.skipIf(
        os.name != "posix" or os.geteuid() == 0,
        "needs POSIX permissions and a non-root user",
    )
    def test_unreadable_subdirectory_is_skipped(self):
        """One unreadable subdirectory used to abort the entire scan."""
        locked = os.path.join(self.root, "a", "b")
        os.chmod(locked, 0)
        self.addCleanup(os.chmod, locked, 0o755)

        parser = self.scan()
        self.assertCountEqual(
            self.rel(parser.output()), ["top.0001.exr", "a/mid.0001.exr"]
        )

    def test_missing_start_directory_still_raises(self):
        """Errors on the starting point itself must still reach the caller."""
        with self.assertRaises(OSError):
            self.scan(os.path.join(self.root, "does-not-exist"))


###############################################################################
# File name handling


class TestFileNames(_TempDirMixin, unittest.TestCase):
    """Regressions in how file names are classified by Seqparse."""

    def test_frame_only_file_name_via_add_file(self):
        """add_file("0001.exr") crashed with a TypeError."""
        parser = get_parser()
        parser.add_file("0001.exr")
        parser.add_file("0002.exr")
        self.assertEqual([str(x) for x in parser.output()], ["0001,0002.exr"])

    def test_frame_only_file_names_on_disk(self):
        """Frame-only files on disk were never grouped into a sequence."""
        self.make_files("0001.exr", "0002.exr", "0003.exr")
        parser = self.scan()
        self.assertEqual(self.rel(parser.output()), ["0001-0003.exr"])

    def test_sequence_like_file_on_disk_is_a_singleton(self):
        """A file literally named "a.1-3.exr" crashed stat caching."""
        self.make_files("a.1-3.exr")
        parser = self.scan(stat=True)
        items = list(parser.output())
        self.assertEqual(self.rel(items), ["a.1-3.exr"])
        self.assertEqual(items[0].size, 0)

    def test_sequence_string_via_add_file_still_supported(self):
        """add_file() with a whole sequence string remains a feature."""
        parser = get_parser()
        parser.add_file("shot.0001-0003.exr")
        self.assertEqual(
            [str(x) for x in parser.output()], ["shot.0001-0003.exr"]
        )


###############################################################################
# Seqparse.output / seqls


class TestOutput(_TempDirMixin, unittest.TestCase):
    """Regressions in Seqparse.output and the seqls long format."""

    def test_missing_skips_sequences_without_gaps(self):
        """output(missing=True) yielded empty sequences (blank seqls lines)."""
        self.make_files("full.0001.exr", "full.0002.exr")
        self.make_files("gappy.0001.exr", "gappy.0003.exr")
        parser = self.scan()
        self.assertEqual(
            self.rel(parser.output(missing=True)), ["gappy.0002.exr"]
        )

    def test_long_format_reports_zero_byte_size(self):
        """0-byte files were reported with a size of "----"."""
        self.make_files("empty.0001.exr")
        lines = seqls.long_format_output(self.scan(stat=True).output())
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("0  "), lines[0])

    def test_long_format_without_stats_has_no_date(self):
        """Entries without stats were shown with the current time."""
        fseq = FileSequence(name="missing", ext="exr", frames=[1], pad=4)
        self.assertEqual(
            seqls.long_format_output([fseq]), ["----  ----  missing.0001.exr"]
        )


###############################################################################
# Frame chunks and frame sequences


class TestFrameSequences(unittest.TestCase):
    """Regressions in FrameSequence."""

    def test_range_and_generator_input(self):
        """range() and generators raised TypeError (docstring example)."""
        self.assertEqual(str(get_sequence(range(5))), "0-4")
        self.assertEqual(str(FrameSequence(x for x in (1, 2, 3))), "1-3")
        seq = FrameSequence(pad=2)
        seq.add(range(3))
        self.assertEqual(str(seq), "00-02")

    def test_frame_zero(self):
        """FrameSequence(0) silently produced an empty sequence."""
        self.assertEqual(list(FrameSequence(0)), ["0"])

    def test_frames_may_exceed_padding_in_strings(self):
        """'001,010,100,1000' raised SeqparsePadError."""
        seq = FrameSequence("001,010,100,1000")
        self.assertEqual(seq.pad, 3)
        self.assertEqual(sorted(map(int, seq)), [1, 10, 100, 1000])
        self.assertEqual(str(seq), "001,010,100,1000")

    def test_incorrectly_padded_strings_still_rejected(self):
        """Loosening the rule above must not accept genuinely bad padding."""
        for bad in ("001,0010", "001,5", "001-0010"):
            with self.subTest(bad=bad), self.assertRaises(SeqparsePadError):
                FrameSequence(bad)

    def test_bad_padding_is_a_value_error(self):
        """SeqparsePadError didn't subclass ValueError."""
        with self.assertRaises(ValueError):
            FrameSequence("001,0010")

    def test_validate_rejects_bad_padding(self):
        """validate_frame_sequence() raised instead of returning None."""
        self.assertIsNone(validate_frame_sequence("001,0010"))
        self.assertEqual(validate_frame_sequence("001,010"), "001,010")


###############################################################################
# File sequences


class TestFileSequences(_TempDirMixin, unittest.TestCase):
    """Regressions in FileSequence."""

    def test_explicit_name_is_not_reparsed(self):
        """Base names that look like sequences ("comp.1.final") got mangled."""
        fseq = FileSequence(
            name=os.path.join("d", "comp.1.final"),
            ext="exr",
            frames=[1, 2],
            pad=4,
        )
        self.assertEqual(fseq.name, "comp.1.final")
        self.assertEqual(fseq.ext, "exr")
        self.assertEqual(
            str(fseq), os.path.join("d", "comp.1.final.0001,0002.exr")
        )

    def test_sole_name_argument_is_still_parsed(self):
        """A full sequence string as the only argument is still parsed."""
        fseq = FileSequence("shot.0001-0003.exr")
        self.assertEqual((fseq.name, fseq.ext, fseq.pad), ("shot", "exr", 4))

    def test_clone_keeps_pad_with_overflowing_frame(self):
        """Cloning re-derived the pad from the frames ("10000" -> pad 5)."""
        parent = FileSequence(name="a", ext="exr", frames=[1, 10000], pad=4)
        clone = FileSequence(parent)
        self.assertEqual(clone.pad, 4)
        self.assertEqual(str(clone), str(parent))

    def test_clone_of_empty_sequence(self):
        """Cloning an empty FileSequence raised ValueError."""
        clone = FileSequence(FileSequence(name="a", ext="exr", pad=4))
        self.assertEqual((clone.name, clone.ext, clone.pad), ("a", "exr", 4))
        self.assertEqual(len(clone), 0)

    def test_clone_copies_stats_and_path(self):
        """Cloning dropped cached disk stats."""
        self.make_files("a.0001.exr", content="12345")
        parent = FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[1], pad=4
        )
        parent.stat(1, lazy=True)
        clone = FileSequence(parent)
        self.assertEqual(clone.path, parent.path)
        self.assertEqual(clone.size, 5)

    def test_partially_statted_sequence(self):
        """str() crashed when only some frames had cached stats."""
        self.make_files("a.0001.exr", content="123")
        fseq = FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[1, 2], pad=4
        )
        fseq.stat(1, lazy=True)
        self.assertTrue(str(fseq).endswith("a.0001,0002.exr"))
        self.assertEqual(fseq.size, 3)

    def test_discard_string_frame_drops_stat(self):
        """discard("0001") left the frame's stats behind."""
        self.make_files("a.0001.exr", "a.0002.exr")
        fseq = FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[1, 2], pad=4
        )
        fseq.stat(1, lazy=True)
        fseq.stat(2, lazy=True)
        fseq.discard("0001")
        self.assertEqual(list(fseq.stat()), [2])

    def test_stat_frame_zero(self):
        """Frame 0 produced an empty file name, so stat(0) failed."""
        self.make_files("a.0000.exr", content="xy")
        fseq = FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[0], pad=4
        )
        self.assertEqual(fseq.stat(0, lazy=True).st_size, 2)
        self.assertEqual(fseq.stat("0000").st_size, 2)

    def test_invert_keeps_dotted_name(self):
        """invert() re-parsed full_name, mangling sequence-like base names."""
        fseq = FileSequence(
            name="comp.1.final", ext="exr", frames=[1, 3], pad=4
        )
        inverted = fseq.invert()
        self.assertEqual(str(inverted), "comp.1.final.0002.exr")


###############################################################################
# Containers


class TestContainers(unittest.TestCase):
    """Regressions in FileSequenceContainer and SingletonContainer."""

    def test_multiple_extensions_can_be_output(self):
        """Sorting FileExtension instances raised TypeError."""
        container = FileSequenceContainer(name="foo", file_path="d")
        container["tif"][4].add(1)
        container["exr"][4].add(1)
        self.assertEqual(
            [str(x) for x in container.output()],
            [
                os.path.join("d", "foo.0001.exr"),
                os.path.join("d", "foo.0001.tif"),
            ],
        )

    def test_setitem_keeps_extension_name(self):
        """__setitem__ overwrote the extension's name with the base name."""
        container = FileSequenceContainer(name="foo", file_path="d")
        container["exr"] = FileExtension(name="exr")
        self.assertEqual(container["exr"].name, "exr")
        self.assertIs(container["exr"].parent, container)

        container["exr"][4].add(1)
        self.assertEqual(
            [str(x) for x in container.output()],
            [os.path.join("d", "foo.0001.exr")],
        )

    def test_singleton_discard_drops_stat(self):
        """SingletonContainer.discard() left the file's stats behind."""
        singletons = SingletonContainer(["pony.py"], file_path="d")
        singletons.cache_stat("pony.py", os.stat(__file__))
        singletons.discard("pony.py")
        self.assertNotIn("pony.py", singletons)
        self.assertEqual(singletons.stat(), {})

    def test_membership_does_not_create_entries(self):
        """`in` and .get() on containers were always truthy and added keys."""
        container = FileSequenceContainer(name="foo", file_path="d")
        self.assertNotIn("exr", container)
        self.assertIsNone(container.get("exr"))
        self.assertEqual(list(container), [])

        extension = FileExtension(name="exr")
        self.assertNotIn(4, extension)
        self.assertEqual(extension.get(4, "missing"), "missing")
        self.assertEqual(list(extension), [])

        # Indexing still creates entries on demand, like defaultdict.
        container["exr"][4].add(1)
        self.assertIn("exr", container)
        self.assertIn(4, container["exr"])

    def test_wrong_value_type_is_a_type_error(self):
        """Containers raised ValueError (not TypeError) for wrong types."""
        with self.assertRaises(TypeError):
            FileSequenceContainer(name="foo")["exr"] = []
        with self.assertRaises(TypeError):
            FileExtension(name="exr")[4] = "foo.0001.exr"


class TestFileSequenceErrors(unittest.TestCase):
    """Regressions in the exception types FileSequence raises."""

    def test_missing_extension_is_a_value_error(self):
        """A missing extension raised AttributeError, fooling hasattr()."""
        fseq = FileSequence(frames="0001-0003")
        with self.assertRaises(ValueError):
            str(fseq)
