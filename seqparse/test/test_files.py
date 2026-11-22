"""Test the File class."""

import os
import unittest
from unittest import mock

from ..files import File
from . import mock_os_stat

###############################################################################
# class: TestFiles


class TestFiles(unittest.TestCase):
    """Test basic functionality on the File class."""

    _test_ext = "py"
    _test_name = "test"
    _test_path = "/pretty/kitty".replace("/", os.sep)

    def setUp(self):
        """Set up the test instance."""

    def test_initialization(self):
        """File: Test initialization of an instance by file name."""
        file_name = "test.0001.py"
        full_name = os.path.join(self._test_path, file_name)

        entry = File(full_name)

        self.assertEqual(entry.full_name, full_name)
        self.assertEqual(entry.name, file_name)
        self.assertEqual(entry.path, self._test_path)
        self.assertEqual(str(entry), full_name)

        self.assertIsNone(entry.mtime)
        self.assertIsNone(entry.size)
        self.assertIsNone(entry.stat())

    @mock.patch("seqparse.sequences.os.stat")
    def test_stat_queries(self, mock_api_call):
        """File: Test stat setting and queries."""
        mock_api_call.side_effect = mock_os_stat

        file_name = "test.0001.py"
        full_name = os.path.join(self._test_path, file_name)

        entry = File(full_name)

        stat = entry.stat()
        self.assertIsNone(stat)

        stat = entry.stat(lazy=True)
        self.assertEqual(stat.st_size, 7975)
        self.assertEqual(stat.st_mtime, 1490908305)
        self.assertEqual(entry.size, 7975)
        self.assertEqual(entry.mtime, 1490908305)

        entry = File(full_name)
        stat = entry.stat(force=True)
        self.assertEqual(entry.stat().st_size, 7975)
        self.assertEqual(entry.stat().st_mtime, 1490908305)
        self.assertEqual(entry.size, 7975)
        self.assertEqual(entry.mtime, 1490908305)

        entry = File(full_name, stat=stat)
        self.assertEqual(entry.stat().st_size, 7975)
        self.assertEqual(entry.stat().st_mtime, 1490908305)
        self.assertEqual(entry.size, 7975)
        self.assertEqual(entry.mtime, 1490908305)

    def test_sorting(self):
        """File: Test instance sorting."""
        file1 = File("/golly/gosh/geewhiz.txt")
        file2 = File("/golly/gosh/geewhiz.txt")
        file3 = File("/golly/gosh/geewhillickers.txt")

        str3 = "/golly/gosh/geewhillickers.txt"

        self.assertLess(file3, file1)
        self.assertEqual(file2, file1)
        self.assertGreater(str3, file2)
        self.assertGreater(str3, file3)
        with self.assertRaises(AssertionError):
            self.assertEqual(str3, file3)

    def test_hashing(self):
        """File: Equal instances hash equally (usable in sets and dicts)."""
        file1 = File("/golly/gosh/geewhiz.txt")
        file2 = File("/golly/gosh/geewhiz.txt")
        file3 = File("/golly/gosh/geewhillickers.txt")

        self.assertEqual(hash(file1), hash(file2))
        self.assertEqual(len({file1, file2, file3}), 2)
        self.assertEqual({file1: "found"}[file2], "found")
