"""Test file sequence discovery on disk."""

# Standard Libraries
import os
import unittest

# Third Party Libraries
import mock

from seqparse import get_parser, validate_frame_sequence


def _generate_files(name="dog", ext="jpg", frames=None):
    """Generate some file sequences for seqparse testing."""
    if frames is None:
        frames = {4: [0]}

    file_names = set()

    for pad, frame_list in frames.iteritems():
        for frame in frame_list:
            file_names.add("%s.%0*d.%s" % (name, pad, frame, ext))

    # Casting the set() to a list() so that we're pretty much guaranteed a non-
    # sorted list of files.
    return list(file_names)


###############################################################################
# class: TestSeqparseModule


class TestSeqparseModule(unittest.TestCase):
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
        self.assertEqual(self._source_path, file_names[self._source_path].path)
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
        self.assertEqual(test_output[0], final_output)

        self.assertIn(self._source_ext, file_seq)
        self.assertEqual(len(file_seq), 1)
        self.assertTrue(4 in file_seq[self._source_ext])
        self.assertEqual(len(file_seq[self._source_ext]), 1)

        # And finally, the frame sequence.
        frame_seq = file_seq[self._source_ext][4]

        self.assertEqual(len(frame_seq), len(frames[4]))
        self.assertEqual(str(frame_seq), frame_seq_output)

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_scan_path__complex1(self, mock_walk):
        """Test complex file sequence discovery from disk location."""
        frames = {
            1: [5, 6, 7, 8, 114, 199, 2000],
            3: [8, 9, 10, 12],
            4: [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 101]
        }

        input_files = _generate_files(
            ext=self._source_ext, frames=frames, name=self._source_file_name)

        # Expected output frame sequences. Note how frames 114, 199 move to the
        # "pad 3" group and 2000 moves to the "pad 4" group!
        output_seqs = {
            1: "5-8",
            3: "008-010,012,114,199",
            4: "0000-0006,0008-0012x2,0101,2000"
        }

        # Expected final output (where "/" is os.sep):
        # test_dir/TEST_DIR.5-8.exr
        # test_dir/TEST_DIR.008-010,012,114,199.exr
        # test_dir/TEST_DIR.0000-0006,0008-0012x2,0101,2000.exr

        mock_walk.return_value = [(self._source_path, (), input_files)]

        parser = get_parser()
        parser.scan_path(self._source_path)

        final_output = list()
        for pad, seq_frames in sorted(output_seqs.items()):
            bits = (self._source_file_name, seq_frames, self._source_ext)
            final_output.append(
                os.path.join(self._source_path, ".".join(bits)))

        data = parser.sequences

        # Check the structure of the sequences property.
        self.assertIn(self._source_path, data)
        self.assertEqual(len(data), 1)
        self.assertIn(self._source_file_name, data[self._source_path])
        self.assertEqual(len(data[self._source_path]), 1)

        # Now check the file sequence itself.
        file_seq = data[self._source_path][self._source_file_name]

        test_output = list(file_seq.output())
        self.assertEqual(len(test_output), 3)
        self.assertEqual(test_output, final_output)

        self.assertIn(self._source_ext, file_seq)
        self.assertEqual(len(file_seq), 1)
        self.assertEqual(set(file_seq[self._source_ext]), set(output_seqs))

        # And finally, the frame sequences.
        for pad in sorted(output_seqs):
            self.assertEqual(output_seqs[pad],
                             str(file_seq[self._source_ext][pad]))

    def test_valid_frame_sequences(self):
        """Test validity of simple frame ranges."""
        good_frame_seqs = [
            "0001", ",0001", "0001,", "0001-0001", "0001-0001x0",
            "0001-0003x3", "0001,0003", "0001,,0003", "0001-0010",
            "0001-0010x0", "0001-0011x2", "0001-0012x2", "0001-0005,0007-0010",
            "0001-0005x2,0007-0010", "0001-0005,0007-0011x2",
            "0001-0005,0006,0008-0012x2", "0001,0003-0007,0009-0015x2"
        ]
        bad_frame_seqs = [
            "-0001", "0001-", "0001x2", "x2", "0001,0003x2", "0001-0005x",
            "0010-0001", "x", ",", ",,", ""
        ]

        print "\n  GOOD SEQUENCES\n  --------------"
        for frame_seq in good_frame_seqs:
            output = validate_frame_sequence(frame_seq)
            print '  o "%s" --> %s' % (frame_seq, output)
            self.assertTrue(output)

        print "\n  BAD SEQUENCES\n  -------------"
        for frame_seq in bad_frame_seqs:
            print '  o "%s"' % frame_seq
            self.assertFalse(validate_frame_sequence(frame_seq))
