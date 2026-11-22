"""
Windows path handling, simulated on any OS.

Each seqparse module's `os` is swapped for a copy that uses Windows path
rules (ntpath, "\\" with "/" as the alternate separator), so drive letters,
UNC shares and mixed separators are tested everywhere. Real Windows runs in
CI as well.
"""

from collections.abc import Iterator
import contextlib
import ntpath
import os
import types
import unittest
from unittest import mock

from seqparse import get_parser
from seqparse import seqparse as seqparse_module
import seqparse.containers
import seqparse.files
from seqparse.files import File
import seqparse.sequences
from seqparse.sequences import FileSequence

_MODULES = (
    seqparse.containers,
    seqparse.files,
    seqparse_module,
    seqparse.sequences,
)


@contextlib.contextmanager
def windows_paths() -> Iterator[None]:
    """Make seqparse use Windows path rules for the duration."""
    fake_os = types.SimpleNamespace(**vars(os))
    fake_os.path = ntpath
    fake_os.sep, fake_os.altsep = "\\", "/"
    with contextlib.ExitStack() as stack:
        for module in _MODULES:
            stack.enter_context(mock.patch.object(module, "os", fake_os))
        stack.enter_context(
            mock.patch.object(
                seqparse_module, "_split", seqparse_module._split_native
            )
        )
        yield


class TestWindowsFileSequence(unittest.TestCase):
    """FileSequence names and paths under Windows rules."""

    def test_drive_path_in_name(self):
        """A name with a drive and backslashes splits into path and name."""
        with windows_paths():
            fseq = FileSequence(
                name="C:\\renders\\plate", ext="exr", frames=[1, 2], pad=4
            )
            self.assertEqual(fseq.path, "C:\\renders")
            self.assertEqual(fseq.name, "plate")
            self.assertEqual(str(fseq), "C:\\renders\\plate.0001,0002.exr")

    def test_forward_slashes_in_name(self):
        """Forward slashes are separators on Windows too."""
        with windows_paths():
            fseq = FileSequence(name="renders/plate", ext="exr", frames=[1])
            self.assertEqual((fseq.path, fseq.name), ("renders", "plate"))
            self.assertEqual(fseq.full_name, "renders\\plate")

    def test_unc_path(self):
        """UNC shares keep their leading double backslash."""
        with windows_paths():
            fseq = FileSequence(
                name="\\\\server\\share\\shots\\plate", ext="exr", frames=[7]
            )
            self.assertEqual(fseq.path, "\\\\server\\share\\shots")
            self.assertEqual(str(fseq), "\\\\server\\share\\shots\\plate.7.exr")

    def test_membership_with_either_separator(self):
        """File names match whichever separator they use."""
        with windows_paths():
            fseq = FileSequence(
                name="C:\\r\\plate", ext="exr", frames=[1, 2], pad=4
            )
            self.assertIn("C:\\r\\plate.0001.exr", fseq)
            self.assertIn("C:/r/plate.0002.exr", fseq)
            self.assertNotIn("C:/r/plate.0003.exr", fseq)
            self.assertNotIn("D:/r/plate.0001.exr", fseq)

    def test_file(self):
        """File splits Windows paths."""
        with windows_paths():
            file = File("C:\\r\\notes.txt")
            self.assertEqual((file.path, file.name), ("C:\\r", "notes.txt"))


class TestWindowsSeqparse(unittest.TestCase):
    """Seqparse grouping and scanning under Windows rules."""

    def test_mixed_separators_share_a_directory(self):
        """'C:/r' and 'C:\\r' are one directory: one sequence, one group."""
        with windows_paths():
            parser = get_parser()
            parser.add_file("C:/r/plate.0001.exr")
            parser.add_file("C:\\r\\plate.0002.exr")
            parser.add_file("C:/r/readme.txt")
            output = [str(item) for item in parser.output()]
        self.assertEqual(
            output, ["C:\\r\\plate.0001,0002.exr", "C:\\r\\readme.txt"]
        )
        self.assertEqual(list(parser.locations), ["C:\\r"])

    def test_strip_trailing_separators_keeps_roots(self):
        """Drive roots and UNC shares survive; other trailing seps go."""
        cases = {
            "C:\\": "C:\\",
            "C:/": "C:/",
            "C:": "C:",
            "C:\\renders\\": "C:\\renders",
            "C:\\renders/": "C:\\renders",
            "\\\\server\\share\\": "\\\\server\\share\\",
            "\\\\server\\share\\shots\\": "\\\\server\\share\\shots",
            "renders\\": "renders",
        }
        with windows_paths():
            for path, expected in cases.items():
                with self.subTest(path=path):
                    self.assertEqual(
                        seqparse_module._strip_trailing_sep(path), expected
                    )


class TestPosixRoots(unittest.TestCase):
    """The same helper under the real (POSIX here) rules."""

    @unittest.skipIf(os.name == "nt", "POSIX path rules")
    def test_posix_roots(self):
        """'/' stays a root; trailing slashes go."""
        strip = seqparse_module._strip_trailing_sep
        self.assertEqual(strip("/"), "/")
        self.assertEqual(strip("//"), "//")
        self.assertEqual(strip("/a/b//"), "/a/b")
        self.assertEqual(strip("a\\"), "a\\")  # backslash is a filename char
