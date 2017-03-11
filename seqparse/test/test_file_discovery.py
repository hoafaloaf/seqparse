"""Test file sequence discovery on disk."""

# Standard Libraries
import os
import unittest

# Third Party Libraries
import mock

from seqparse import get_parser


def _generate_files(name="dog", ext="jpg", frames=None):
    """Generate some file sequences for seqparse testing."""
    if frames is None:
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

    _source_ext = "exr"
    _source_file_name = "TEST_DIR"
    _source_path = "test_dir"
    _singletons = ["singleton0.jpg", "singleton1.jpg"]

    def setUp(self):
        """Set up the test case."""
        pass

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_scan_path_singletons(self, mock_walk):
        """Test file singleton discovery from disk location."""
        mock_walk.return_value = [(self._source_path, (), self._singletons)]

        # Expected outputs ...
        output = [os.path.join(self._source_path, x) for x in self._singletons]

        parser = get_parser()
        parser.scan_path(self._source_path)

        file_names = parser.singletons

        self.assertIn(self._source_path, file_names)
        self.assertEqual(len(file_names), 1)
        self.assertEqual(
            len(file_names[self._source_path]), len(self._singletons))
        self.assertEqual(
            sorted(self._singletons), sorted(file_names[self._source_path]))

        # Check parser output ...
        self.assertEqual(sorted(parser.output()), output)

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_scan_path_sequences_simple(self, mock_walk):
        """Test simple file sequence discovery from disk location."""
        frames = {4: [0, 1, 2, 3, 4]}

        # Expected outputs ...
        frame_seq_output = "0000-0004"
        file_seq_output = ".".join(
            (self._source_file_name, frame_seq_output, self._source_ext))
        final_output = os.path.join(self._source_path, file_seq_output)

        input_files = _generate_files(
            ext=self._source_ext, frames=frames, name=self._source_file_name)

        mock_walk.return_value = [(self._source_path, (), input_files)]

        parser = get_parser()
        parser.scan_path(self._source_path)

        data = parser.sequences

        test_output = list(parser.output())
        self.assertEqual(len(test_output), 1)
        self.assertEqual(test_output[0], final_output)

        # Check the structure of the sequences property.
        self.assertIn(self._source_path, data)
        self.assertEqual(len(data), 1)
        self.assertIn(self._source_file_name, data[self._source_path])
        self.assertEqual(len(data[self._source_path]), 1)

        # Now check the file sequence itself.
        file_seq = data[self._source_path][self._source_file_name]

        test_output = list(file_seq.output())
        self.assertEqual(len(test_output), 1)
        self.assertEqual(test_output[0], file_seq_output)

        self.assertIn(self._source_ext, file_seq)
        self.assertEqual(len(file_seq), 1)
        self.assertTrue(4 in file_seq[self._source_ext])
        self.assertEqual(len(file_seq[self._source_ext]), 1)

        # And finally, the frame sequence.
        frame_seq = file_seq[self._source_ext][4]

        self.assertEqual(len(frame_seq), len(frames[4]))
        self.assertEqual(str(frame_seq), frame_seq_output)
