"""Test file sequence discovery on disk."""

# Standard Libraries
import os
import unittest

# Third Party Libraries
import mock

from seqparse import get_parser


def _generate_files(name="dog", ext="jpg"):
    """Generate some file sequences for seqparse testing."""
    frames = {
        4: [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 101],
        3: [8, 9, 10, 12],
        1: [5, 6, 7, 8, 114, 199, 2000]
    }

    file_names = set()

    for pad, frame_list in frames.iteritems():
        for frame in frame_list:
            file_names.add("%s.%0*d.%s" % (name, pad, frame, ext))

    # Casting the set() to a list() so that we're pretty much guaranteed a non-
    # sorted list of files.
    return list(file_names)


###############################################################################
# class: TestFileDiscovery


class TestFileDiscovery(unittest.TestCase):
    """Test file discovery on the seqparse module."""

    _singletons = ["singleton0.jpg", "singleton1.jpg"]
    _source_path = "test_dir"

    def setUp(self):
        """Set up the test case."""
        self._file_names = _generate_files(self._source_path)
        self._file_names.extend(self._singletons)

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_scan_path_singletons(self, mock_walk):
        """Test file discovery from disk location."""
        mock_walk.return_value = [(self._source_path, (), self._singletons)]

        seqs = get_parser()
        seqs.scan_path(self._source_path)

        file_names = seqs.singletons

        self.assertIn(self._source_path, file_names)
        self.assertEqual(len(file_names), 1)
        self.assertEqual(
            len(file_names[self._source_path]), len(self._singletons))
        self.assertEqual(
            sorted(self._singletons), sorted(file_names[self._source_path]))
