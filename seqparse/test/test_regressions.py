"""Regression tests for bugs fixed in the seqparse library.

Each test pins down one previously broken behaviour. Filesystem-related tests
use real temporary directories (not mocked scandir) since symlinks, permissions
and path handling are exactly what the mocks could not exercise.
"""

import base64
import os
import pathlib
import pickle
import tempfile
import unittest
from unittest import mock
import weakref

import seqparse
from seqparse import containers, files, sequences
from seqparse import seqparse as seqparse_module
from seqparse.cli import seqls


def _posix(path):
    """A path with native separators written with "/", for comparisons."""
    return path.replace(os.sep, "/")


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
        parser = seqparse.get_parser()
        parser.scan_options["stat"] = stat
        parser.scan_path(self.root if path is None else path, **kwargs)
        return parser

    def rel(self, items):
        """Parser output relative to the temp directory, with "/" separators."""
        return [_posix(os.path.relpath(str(x), self.root)) for x in items]


###############################################################################
# Directory scanning


class TestPathlibObjects(_TempDirMixin, unittest.TestCase):
    """pathlib objects work wherever a path is accepted (GitHub issue #2).

    With 1.0.1, scan_path(Path) raised AttributeError.
    """

    def setUp(self):
        """Three frames."""
        super().setUp()
        self.make_files("plate.0001.exr", "plate.0002.exr", "plate.0003.exr")
        self.root_path = pathlib.Path(self.root)

    def test_scan_path_takes_a_path(self):
        """A single Path."""
        parser = self.scan(self.root_path)
        self.assertEqual(self.rel(parser.output()), ["plate.0001-0003.exr"])

    def test_scan_path_takes_a_list_of_paths(self):
        """A list of Paths, and a subdirectory."""
        parser = seqparse.get_parser()
        parser.scan_path([self.root_path, self.root_path / "."])
        self.assertEqual(self.rel(parser.output()), ["plate.0001-0003.exr"])

    def test_add_file_takes_a_path(self):
        """Files added one by one."""
        parser = seqparse.get_parser()
        for number in (1, 2):
            parser.add_file(self.root_path / f"plate.{number:04d}.exr")
        self.assertEqual(self.rel(parser.output()), ["plate.0001,0002.exr"])

    def test_the_classes_take_paths_too(self):
        """FileSequence and File."""
        fseq = sequences.FileSequence(
            name=self.root_path / "plate", ext="exr", frames=[1, 2], pad=4
        )
        self.assertEqual(self.rel([fseq]), ["plate.0001,0002.exr"])
        file = files.File(self.root_path / "plate.0001.exr")
        self.assertEqual(self.rel([file]), ["plate.0001.exr"])


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

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unsupported")
    def test_symlinked_directory_reported_under_both_paths(self):
        """The loop guard hid any directory reachable by a second path."""
        os.symlink(
            os.path.join(self.root, "a", "b"), os.path.join(self.root, "alias")
        )
        parser = self.scan()
        self.assertCountEqual(
            self.rel(parser.output()),
            [
                "top.0001.exr",
                "a/mid.0001.exr",
                "a/b/low.0001.exr",
                "alias/low.0001.exr",
            ],
        )

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
        parser = seqparse.get_parser()
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

    def test_single_file_scan_matches_directory_scan(self):
        """Scanning "a.1-3.exr" directly reported a 3-frame sequence."""
        self.make_files("a.1-3.exr", content="abc")
        results = []
        for path in (os.path.join(self.root, "a.1-3.exr"), self.root):
            items = list(self.scan(path, stat=True).output())
            results.append([(type(x).__name__, x.size) for x in items])
        self.assertEqual(results[0], [("File", 3)])
        self.assertEqual(results[0], results[1])

    def test_sequence_string_via_add_file_still_supported(self):
        """add_file() with a whole sequence string remains a feature."""
        parser = seqparse.get_parser()
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
        fseq = sequences.FileSequence(
            name="missing", ext="exr", frames=[1], pad=4
        )
        self.assertEqual(
            seqls.long_format_output([fseq]), ["----  ----  missing.0001.exr"]
        )


###############################################################################
# Frame chunks and frame sequences


class TestFrameSequences(unittest.TestCase):
    """Regressions in FrameSequence."""

    def test_range_and_generator_input(self):
        """range() and generators raised TypeError (docstring example)."""
        self.assertEqual(str(seqparse.get_sequence(range(5))), "0-4")
        self.assertEqual(
            str(sequences.FrameSequence(x for x in (1, 2, 3))), "1-3"
        )
        seq = sequences.FrameSequence(pad=2)
        seq.add(range(3))
        self.assertEqual(str(seq), "00-02")

    def test_frame_zero(self):
        """FrameSequence(0) silently produced an empty sequence."""
        self.assertEqual(list(sequences.FrameSequence(0)), ["0"])

    def test_frames_may_exceed_padding_in_strings(self):
        """'001,010,100,1000' raised SeqparsePadError."""
        seq = sequences.FrameSequence("001,010,100,1000")
        self.assertEqual(seq.pad, 3)
        self.assertEqual(sorted(map(int, seq)), [1, 10, 100, 1000])
        self.assertEqual(str(seq), "001,010,100,1000")

    def test_incorrectly_padded_strings_still_rejected(self):
        """Loosening the rule above must not accept genuinely bad padding."""
        for bad in ("001,0010", "001,5", "001-0010"):
            with (
                self.subTest(bad=bad),
                self.assertRaises(sequences.SeqparsePadError),
            ):
                sequences.FrameSequence(bad)

    def test_bad_padding_is_a_value_error(self):
        """SeqparsePadError didn't subclass ValueError."""
        with self.assertRaises(ValueError):
            sequences.FrameSequence("001,0010")

    def test_validate_rejects_bad_padding(self):
        """validate_frame_sequence() raised instead of returning None."""
        self.assertIsNone(seqparse.validate_frame_sequence("001,0010"))
        self.assertEqual(seqparse.validate_frame_sequence("001,010"), "001,010")


###############################################################################
# File sequences


class TestFileSequences(_TempDirMixin, unittest.TestCase):
    """Regressions in FileSequence."""

    def test_explicit_name_is_not_reparsed(self):
        """Base names that look like sequences ("comp.1.final") got mangled."""
        fseq = sequences.FileSequence(
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
        fseq = sequences.FileSequence("shot.0001-0003.exr")
        self.assertEqual((fseq.name, fseq.ext, fseq.pad), ("shot", "exr", 4))

    def test_full_name_with_matching_ext_is_parsed(self):
        """A full sequence string plus a redundant ext wasn't parsed."""
        fseq = sequences.FileSequence("foo.0001-0003.exr", ext="exr")
        self.assertEqual((fseq.name, fseq.ext, len(fseq)), ("foo", "exr", 3))

        # A conflicting ext means the name is just a base name.
        fseq = sequences.FileSequence("comp.1.final", ext="exr")
        self.assertEqual(
            (fseq.name, fseq.ext, len(fseq)), ("comp.1.final", "exr", 0)
        )

    def test_clone_keeps_pad_with_overflowing_frame(self):
        """Cloning re-derived the pad from the frames ("10000" -> pad 5)."""
        parent = sequences.FileSequence(
            name="a", ext="exr", frames=[1, 10000], pad=4
        )
        clone = sequences.FileSequence(parent)
        self.assertEqual(clone.pad, 4)
        self.assertEqual(str(clone), str(parent))

    def test_clone_of_empty_sequence(self):
        """Cloning an empty FileSequence raised ValueError."""
        clone = sequences.FileSequence(
            sequences.FileSequence(name="a", ext="exr", pad=4)
        )
        self.assertEqual((clone.name, clone.ext, clone.pad), ("a", "exr", 4))
        self.assertEqual(len(clone), 0)

    def test_clone_copies_stats_and_path(self):
        """Cloning dropped cached disk stats."""
        self.make_files("a.0001.exr", content="12345")
        parent = sequences.FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[1], pad=4
        )
        parent.stat(1, lazy=True)
        clone = sequences.FileSequence(parent)
        self.assertEqual(clone.path, parent.path)
        self.assertEqual(clone.size, 5)

    def test_partially_statted_sequence(self):
        """str() crashed when only some frames had cached stats."""
        self.make_files("a.0001.exr", content="123")
        fseq = sequences.FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[1, 2], pad=4
        )
        fseq.stat(1, lazy=True)
        self.assertTrue(str(fseq).endswith("a.0001,0002.exr"))
        self.assertEqual(fseq.size, 3)

    def test_discard_string_frame_drops_stat(self):
        """discard("0001") left the frame's stats behind."""
        self.make_files("a.0001.exr", "a.0002.exr")
        fseq = sequences.FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[1, 2], pad=4
        )
        fseq.stat(1, lazy=True)
        fseq.stat(2, lazy=True)
        fseq.discard("0001")
        self.assertEqual(list(fseq.stat()), [2])

    def test_stat_frame_zero(self):
        """Frame 0 produced an empty file name, so stat(0) failed."""
        self.make_files("a.0000.exr", content="xy")
        fseq = sequences.FileSequence(
            name=os.path.join(self.root, "a"), ext="exr", frames=[0], pad=4
        )
        self.assertEqual(fseq.stat(0, lazy=True).st_size, 2)
        self.assertEqual(fseq.stat("0000").st_size, 2)

    def test_invert_keeps_dotted_name(self):
        """invert() re-parsed full_name, mangling sequence-like base names."""
        fseq = sequences.FileSequence(
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
        container = containers.FileSequenceContainer(name="foo", file_path="d")
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
        container = containers.FileSequenceContainer(name="foo", file_path="d")
        container["exr"] = containers.FileExtension(name="exr")
        self.assertEqual(container["exr"].name, "exr")
        self.assertIs(container["exr"].parent, container)

        container["exr"][4].add(1)
        self.assertEqual(
            [str(x) for x in container.output()],
            [os.path.join("d", "foo.0001.exr")],
        )

    def test_singleton_discard_drops_stat(self):
        """SingletonContainer.discard() left the file's stats behind."""
        singletons = containers.SingletonContainer(["pony.py"], file_path="d")
        singletons.cache_stat("pony.py", os.stat(__file__))
        singletons.discard("pony.py")
        self.assertNotIn("pony.py", singletons)
        self.assertEqual(singletons.stat(), {})

    def test_membership_does_not_create_entries(self):
        """`in` and .get() on containers were always truthy and added keys."""
        container = containers.FileSequenceContainer(name="foo", file_path="d")
        self.assertNotIn("exr", container)
        self.assertIsNone(container.get("exr"))
        self.assertEqual(list(container), [])

        extension = containers.FileExtension(name="exr")
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
            containers.FileSequenceContainer(name="foo")["exr"] = []
        with self.assertRaises(TypeError):
            containers.FileExtension(name="exr")[4] = "foo.0001.exr"

    def test_assigned_extension_adopts_existing_sequences(self):
        """Sequences already in an assigned FileExtension lost their names."""
        extension = containers.FileExtension(name="exr")
        extension[4] = [1, 2, 3]
        container = containers.FileSequenceContainer(name="foo", file_path="d")
        container["exr"] = extension
        self.assertEqual(
            [str(x) for x in container.output()],
            [os.path.join("d", "foo.0001-0003.exr")],
        )

    def test_empty_parent_still_names_new_sequences(self):
        """An empty (falsy) parent container was ignored when naming."""
        parent = containers.FileSequenceContainer(name="foo", file_path="d")
        extension = containers.FileExtension(name="exr", parent=parent)
        extension[4].add(1)
        self.assertEqual(
            [str(x) for x in extension.output()],
            [os.path.join("d", "foo.0001.exr")],
        )

    def test_pop_and_setdefault_do_not_autocreate(self):
        """pop()/setdefault() went through the auto-creating __getitem__."""
        extension = containers.FileExtension(name="exr")
        self.assertIsNone(extension.pop(4, None))
        with self.assertRaises(KeyError):
            extension.pop(4)
        self.assertEqual(list(extension), [])

        container = containers.FileSequenceContainer(name="foo")
        mine = containers.FileExtension(name="tif")
        self.assertIs(container.setdefault("tif", mine), mine)
        self.assertIs(
            container.setdefault("tif", containers.FileExtension("tif")), mine
        )
        # No default: behaves like indexing and creates an empty child.
        self.assertIsInstance(
            container.setdefault("exr"), containers.FileExtension
        )
        self.assertCountEqual(container, ["exr", "tif"])


class TestFileSequenceErrors(unittest.TestCase):
    """Regressions in the exception types FileSequence raises."""

    def test_missing_extension_is_a_value_error(self):
        """A missing extension raised AttributeError, fooling hasattr()."""
        fseq = sequences.FileSequence(frames="0001-0003")
        with self.assertRaises(ValueError):
            str(fseq)


class TestFrameStorage(unittest.TestCase):
    """Frames are stored compactly; edge cases of that storage."""

    def test_frames_beyond_64_bits(self):
        """Frame numbers too big for a 64-bit array still work."""
        big = 2**70
        seq = sequences.FrameSequence([3, 1, big, 2])
        seq.add(big + 2)
        self.assertEqual(str(seq), f"1-3,{big},{big + 2}")
        self.assertIn(big, seq)
        self.assertNotIn(big + 1, seq)
        seq.discard(big)
        self.assertEqual(len(seq), 4)
        inverted = sequences.FrameSequence([big, big + 3]).invert()
        self.assertEqual(str(inverted), f"{big + 1},{big + 2}")

    def test_interleaved_adds_and_reads(self):
        """Small and large merges, in and out of order, dedupe correctly."""
        seq = sequences.FrameSequence(range(0, 100, 2))
        for frame in (5, 3, 5, 98, 101, 0):
            seq.add(frame)
            self.assertIn(frame, seq)
        seq.update(range(200, 99, -1))  # 101 frames, descending: full merge
        self.assertEqual(len(seq), 50 + 2 + 101)
        self.assertEqual(list(seq)[:4], ["0", "2", "3", "4"])
        seq.discard(3)
        seq.discard(3)
        self.assertNotIn(3, seq)
        self.assertEqual(len(seq), 152)


# Pickles made by seqparse 1.0.x (master at 6ea1a80), protocol 2. Their
# os.stat_result values keep only the fields every OS has: one carrying
# macOS-only fields (st_flags, ...) fails to unpickle on Linux and Windows
# since Python 3.13.
LEGACY_PICKLES = {
    "file": (
        "gAJjc2VxcGFyc2UuZmlsZXMKRmlsZQpxACmBcQF9cQIoWAUAAABfaW5mb3EDfXEE"
        "KFgEAAAAZnVsbHEFWAgAAAAvci9hLnR4dHEGWAQAAABuYW1lcQdYBQAAAGEudHh0"
        "cQhYBAAAAHBhdGhxCVgCAAAAL3JxCnVYBQAAAF9zdGF0cQtjb3MKc3RhdF9yZXN1"
        "bHQKcQwoSwFLAUsBSwFLAUsBSwFLAUsBSwF0cQ19cQ4oWAgAAABzdF9hdGltZXEP"
        "SwFYCAAAAHN0X210aW1lcRBLAVgIAAAAc3RfY3RpbWVxEUsBdYZxG1JxHHViLg=="
    ),
    "chunk": (
        "gAJjc2VxcGFyc2Uuc2VxdWVuY2VzCkZyYW1lQ2h1bmsKcQApgXEBfXECKFgFAAAA"
        "X2RhdGFxA31xBChYBQAAAGZpcnN0cQVLBVgEAAAAbGFzdHEGSwtYBgAAAGxlbmd0"
        "aHEHSwRYAwAAAHBhZHEISwNYBAAAAHN0ZXBxCUsCdVgHAAAAX291dHB1dHEKWAkA"
        "AAAwMDUtMDExeDJxC3ViLg=="
    ),
    "frames": (
        "gAJjc2VxcGFyc2Uuc2VxdWVuY2VzCkZyYW1lU2VxdWVuY2UKcQApgXEBfXECKFgG"
        "AAAAX2F0dHJzcQN9cQQoWAYAAABjaHVua3NxBV1xBlgFAAAAZGlydHlxB4hYCQAA"
        "AGlzX3BhZGRlZHEIiVgDAAAAcGFkcQlLAlgEAAAAc3RhdHEKfXELdVgFAAAAX2Rh"
        "dGFxDGNfX2J1aWx0aW5fXwpzZXQKcQ1dcQ4oSwFLAksDSwdlhXEPUnEQWAcAAABf"
        "b3V0cHV0cRFOdWIu"
    ),
    "file_seq": (
        "gAJjc2VxcGFyc2Uuc2VxdWVuY2VzCkZpbGVTZXF1ZW5jZQpxACmBcQF9cQIoWAYA"
        "AABfY2FjaGVxA31xBChYBQAAAGN0aW1lcQVOWAUAAABtdGltZXEGTlgEAAAAc2l6"
        "ZXEHTnVYBQAAAF9pbmZvcQh9cQkoWAMAAABleHRxClgDAAAAZXhycQtYBAAAAGZ1"
        "bGxxDFgIAAAAL3IvcGxhdGVxDVgEAAAAbmFtZXEOWAUAAABwbGF0ZXEPWAQAAABw"
        "YXRocRBYAgAAAC9ycRF1WAUAAABfc3RhdHESfXETSwFjb3MKc3RhdF9yZXN1bHQK"
        "cRQoSwBLAEsASwBLAEsASwBLAEsASwB0cRV9cRYoWAgAAABzdF9hdGltZXEXSwBY"
        "CAAAAHN0X210aW1lcRhLAFgIAAAAc3RfY3RpbWVxGUsAdYZxI1JxJHNYBgAAAF9h"
        "dHRyc3ElfXEmKFgGAAAAY2h1bmtzcSddcShYBQAAAGRpcnR5cSmIWAkAAABpc19w"
        "YWRkZWRxKolYAwAAAHBhZHErSwRYBAAAAHN0YXRxLH1xLXVYBQAAAF9kYXRhcS5j"
        "X19idWlsdGluX18Kc2V0CnEvXXEwKEsBSwJLA0sFZYVxMVJxMlgHAAAAX291dHB1"
        "dHEzTnViLg=="
    ),
}


def _legacy(name):
    """Load one of the seqparse 1.0.x pickles."""
    return pickle.loads(base64.b64decode(LEGACY_PICKLES[name]))


class TestSlotsCompatibility(unittest.TestCase):
    """__slots__ must not break what worked with dict-based instances."""

    def test_weakrefs_and_custom_attributes(self):
        """Weak references and ad-hoc attributes still work."""
        for obj in (
            files.File("/r/a.txt"),
            sequences.FrameChunk(1, 5),
            sequences.FrameSequence([1, 2]),
            sequences.FileSequence(name="a", ext="exr", frames=[1]),
        ):
            self.assertIs(weakref.ref(obj)(), obj)
            obj.custom = 1
            self.assertEqual(obj.custom, 1)

    def test_round_trip_pickle(self):
        """Current pickles round-trip, including custom attributes."""
        seq = sequences.FileSequence(
            name="/r/plate", ext="exr", frames=[1, 3], pad=4
        )
        seq.custom = "x"
        clone = pickle.loads(pickle.dumps(seq))
        self.assertEqual(_posix(str(clone)), "/r/plate.0001,0003.exr")
        self.assertEqual(clone.custom, "x")
        self.assertEqual(
            str(pickle.loads(pickle.dumps(sequences.FrameChunk(1, 9, 2)))),
            "1-9x2",
        )

    def test_legacy_pickles_are_portable(self):
        """The fixtures carry no OS-specific os.stat_result fields."""
        for name, data in LEGACY_PICKLES.items():
            raw = base64.b64decode(data)
            for field in (b"st_flags", b"st_gen", b"st_birthtime", b"st_rdev"):
                self.assertNotIn(field, raw, name)

    def test_legacy_pickles(self):
        """Pickles made by seqparse 1.0.x still load."""
        file = _legacy("file")
        self.assertEqual(
            tuple(map(_posix, (file.full_name, file.name, file.path))),
            ("/r/a.txt", "a.txt", "/r"),
        )
        self.assertEqual(file.size, 1)
        chunk = _legacy("chunk")
        self.assertEqual(
            (str(chunk), len(chunk), chunk.pad), ("005-011x2", 4, 3)
        )
        frames = _legacy("frames")
        self.assertEqual((str(frames), frames.pad), ("01-03,07", 2))
        frames.add(4)
        self.assertEqual(str(frames), "01-04,07")
        fseq = _legacy("file_seq")
        self.assertEqual(_posix(str(fseq)), "/r/plate.0001-0003,0005.exr")
        self.assertEqual(fseq.size, 0)
        self.assertIn(5, fseq)
        # The fixtures were pickled on POSIX, so their paths use "/".
        if os.sep == "/":
            self.assertIn("/r/plate.0005.exr", fseq)


class TestSequenceEdgeCases(unittest.TestCase):
    """Behaviour the array-backed storage must keep."""

    def test_mutating_while_iterating(self):
        """Iteration works on a snapshot, like the old chunk list."""
        seq = sequences.FrameSequence(range(1, 11))
        for frame in seq:
            if int(frame) % 3:
                seq.discard(frame)
        self.assertEqual(str(seq), "3-9x3")
        seq = sequences.FrameSequence([1, 5])
        seen = []
        for frame in seq:
            seen.append(frame)
            seq.add(3)
            len(seq)
        self.assertEqual(seen, ["1", "5"])

    def test_discard_inexact_numbers(self):
        """discard() of a non-integral number removes nothing."""
        seq = sequences.FrameSequence([1, 2, 3])
        seq.discard(1.5)
        self.assertEqual(str(seq), "1-3")
        seq.discard(2.0)
        self.assertEqual(str(seq), "1,3")
        seq.discard(None)
        self.assertEqual(str(seq), "1,3")

    def test_negative_frame_file_names(self):
        """Negative frames are members by file name too."""
        seq = sequences.FileSequence(
            name="foo", frames=[-5, 1], ext="exr", pad=4
        )
        self.assertIn("foo.-005.exr", list(seq))
        self.assertIn("foo.-005.exr", seq)
        self.assertNotIn("foo.-05.exr", seq)

    def test_pad_change_refreshes_output(self):
        """Changing pad after output was calculated updates str()."""
        seq = sequences.FrameSequence([1, 2])
        self.assertEqual(str(seq), "1,2")
        seq.pad = 4
        self.assertEqual(str(seq), "0001,0002")
        self.assertEqual(list(seq), ["0001", "0002"])


class TestScanLoopDetection(unittest.TestCase):
    """Loop detection must not drop directories that merely share inodes."""

    def test_reused_inode_numbers_are_not_loops(self):
        """Same (dev, ino) for different directories (some network mounts)."""
        with tempfile.TemporaryDirectory() as root:
            for sub in ("a", "a/b"):
                os.mkdir(os.path.join(root, sub))
            with open(os.path.join(root, "a", "b", "f.0001.exr"), "w"):
                pass
            with mock.patch.object(
                seqparse_module, "_dir_key", return_value=(1, 1)
            ):
                parser = seqparse.get_parser()
                parser.scan_path(root)
            self.assertEqual(
                [str(x) for x in parser.output()],
                [os.path.join(root, "a", "b", "f.0001.exr")],
            )
