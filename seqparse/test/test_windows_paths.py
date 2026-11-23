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

import seqparse
from seqparse import files, sequences
from seqparse import seqparse as seqparse_module
import seqparse.containers
import seqparse.files
import seqparse.sequences

_MODULES = (
    seqparse.containers,
    seqparse.files,
    seqparse_module,
    seqparse.sequences,
)


class DirEntry:
    """A directory entry of a fake tree (seqparse recognises it by name)."""

    def __init__(self, path, is_file):
        """Initialise the instance."""
        self.path = path
        self.name = ntpath.basename(path)
        self._is_file = is_file

    def is_file(self, follow_symlinks=True):
        """Whether this entry is a file."""
        return self._is_file

    def is_dir(self, follow_symlinks=True):
        """Whether this entry is a directory."""
        return not self._is_file

    def stat(self, follow_symlinks=True):
        """Some stats."""
        return os.stat_result((0o100644, 0, 0, 1, 0, 0, 10, 1, 1, 1))


def _offline(fake_os, tree):
    """
    Serve a tree of {directory: [(name, is_file), ...]} from memory.

    Nothing here may reach a real filesystem or the network: on a real
    Windows machine stat-ing a UNC path with an IP address would try to
    connect to it.
    """

    def no_such_file(path, *args, **kwargs):
        raise FileNotFoundError(path)

    def scandir(path):
        entries = tree[ntpath.normpath(path)]
        return iter(
            [DirEntry(ntpath.join(path, name), f) for name, f in entries]
        )

    offline_path = types.SimpleNamespace(**vars(ntpath))
    offline_path.isfile = lambda path: False
    offline_path.isdir = lambda path: ntpath.normpath(path) in tree
    offline_path.realpath = ntpath.abspath
    fake_os.path = offline_path
    fake_os.scandir = scandir
    fake_os.stat = fake_os.lstat = no_such_file


@contextlib.contextmanager
def windows_paths(tree=None) -> Iterator[None]:
    """
    Make seqparse use Windows path rules for the duration.

    With a tree (see `_offline`) directory scans are served from memory.
    """
    fake_os = types.SimpleNamespace(**vars(os))
    fake_os.path = ntpath
    fake_os.sep, fake_os.altsep = "\\", "/"
    if tree is not None:
        _offline(fake_os, tree)
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
            fseq = sequences.FileSequence(
                name="C:\\renders\\plate", ext="exr", frames=[1, 2], pad=4
            )
            self.assertEqual(fseq.path, "C:\\renders")
            self.assertEqual(fseq.name, "plate")
            self.assertEqual(str(fseq), "C:\\renders\\plate.0001,0002.exr")

    def test_forward_slashes_in_name(self):
        """Forward slashes are separators on Windows too."""
        with windows_paths():
            fseq = sequences.FileSequence(
                name="renders/plate", ext="exr", frames=[1]
            )
            self.assertEqual((fseq.path, fseq.name), ("renders", "plate"))
            self.assertEqual(fseq.full_name, "renders\\plate")

    def test_unc_path(self):
        """UNC shares keep their leading double backslash."""
        with windows_paths():
            fseq = sequences.FileSequence(
                name="\\\\server\\share\\shots\\plate", ext="exr", frames=[7]
            )
            self.assertEqual(fseq.path, "\\\\server\\share\\shots")
            self.assertEqual(str(fseq), "\\\\server\\share\\shots\\plate.7.exr")

    def test_membership_with_either_separator(self):
        """File names match whichever separator they use."""
        with windows_paths():
            fseq = sequences.FileSequence(
                name="C:\\r\\plate", ext="exr", frames=[1, 2], pad=4
            )
            self.assertIn("C:\\r\\plate.0001.exr", fseq)
            self.assertIn("C:/r/plate.0002.exr", fseq)
            self.assertNotIn("C:/r/plate.0003.exr", fseq)
            self.assertNotIn("D:/r/plate.0001.exr", fseq)

    def test_file(self):
        """File splits Windows paths."""
        with windows_paths():
            file = files.File("C:\\r\\notes.txt")
            self.assertEqual((file.path, file.name), ("C:\\r", "notes.txt"))


class TestWindowsSeqparse(unittest.TestCase):
    """Seqparse grouping and scanning under Windows rules."""

    def test_mixed_separators_share_a_directory(self):
        """'C:/r' and 'C:\\r' are one directory: one sequence, one group."""
        with windows_paths():
            parser = seqparse.get_parser()
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


class TestWindowsScanning(unittest.TestCase):
    """Scanning like Windows does: mixed separators, UNC shares, IP servers."""

    # GitHub issue #2: with the 1.0.1 code a UNC path with an IP address
    # came out as "//10.11.11,1001-1073.102/ohufx/..." (the server's digits
    # read as a frame number).
    ROOTS = (
        "//10.11.11.102/ohufx/jobs/show/20220907",
        "\\\\10.11.11.102\\ohufx\\jobs\\show\\20220907",
        "//10.11.11.102/ohufx/jobs/show/20220907/",
        "//server/share/jobs/show/20220907",
        "C:/shots/show/20220907",
    )
    FILES = ("plate.1001.jpg", "plate.1002.jpg", "plate.1003.jpg", "notes.txt")

    def test_unc_paths_with_ip_addresses_are_scanned_correctly(self):
        """The sequence is found and the server's name is left alone."""
        for root in self.ROOTS:
            with self.subTest(root=root):
                top = ntpath.normpath(root)
                inner = ntpath.join(top, "folder_name")
                tree = {
                    top: [("folder_name", False)],
                    inner: [(name, True) for name in self.FILES],
                }
                with windows_paths(tree):
                    parser = seqparse.get_parser()
                    parser.scan_path(root)
                    found = [str(item) for item in parser.output()]
                    locations = sorted(parser.locations)
                self.assertEqual(
                    found,
                    [
                        ntpath.join(inner, "plate.1001-1003.jpg"),
                        ntpath.join(inner, "notes.txt"),
                    ],
                )
                self.assertEqual(locations, [inner])

    def test_names_with_mixed_separators_share_one_directory(self):
        """Forward and backward slashes name the same directory."""
        with windows_paths():
            parser = seqparse.get_parser()
            parser.add_file(
                "//10.11.11.102/ohufx/jobs/20220907\\f\\plate.1001.jpg"
            )
            parser.add_file(
                "//10.11.11.102/ohufx/jobs/20220907/f/plate.1002.jpg"
            )
            found = [str(item) for item in parser.output()]
        self.assertEqual(
            found,
            ["\\\\10.11.11.102\\ohufx\\jobs\\20220907\\f\\plate.1001,1002.jpg"],
        )
