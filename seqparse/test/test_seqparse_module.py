"""Test file sequence discovery on disk."""

# Standard Libraries
import os
import unittest

# Third Party Libraries
import mock

from . import generate_files, mock_walk_deep
from .. import get_parser, validate_frame_sequence

###############################################################################
# class: TestSeqparseModule


class TestSeqparseModule(unittest.TestCase):
    """Test file discovery on the seqparse module."""

    _test_ext = "exr"
    _test_file_name = "TEST_DIR"
    _test_root = "test_dir"
    _singletons = ["singleton0.jpg", "singleton1.jpg"]

    def setUp(self):
        """Set up the test case."""
        pass

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_singletons(self, mock_api_call):
        """Test file singleton discovery from disk location."""
        mock_api_call.return_value = [(self._test_root, [], self._singletons)]

        # Expected outputs ...
        output = [os.path.join(self._test_root, x) for x in self._singletons]

        parser = get_parser()
        parser.scan_path(self._test_root)

        file_names = parser.singletons

        self.assertIn(self._test_root, file_names)
        self.assertEqual(self._test_root, file_names[self._test_root].path)
        self.assertEqual(len(file_names), 1)
        self.assertEqual(
            len(file_names[self._test_root]), len(self._singletons))
        self.assertEqual(
            sorted(self._singletons), sorted(file_names[self._test_root]))

        # Check parser output ...
        self.assertEqual(sorted(parser.output()), output)

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_single_padded_file(self, mock_api_call):
        """Test single padded file sequence discovery from disk location."""
        frames = {4: [1]}

        # Expected outputs ...
        frame_seq_output = "0001"
        file_seq_output = ".".join(
            (self._test_file_name, frame_seq_output, self._test_ext))
        final_output = os.path.join(self._test_root, file_seq_output)

        input_files = generate_files(
            ext=self._test_ext, frames=frames, name=self._test_file_name)

        mock_api_call.return_value = [(self._test_root, [], input_files)]

        parser = get_parser()
        parser.scan_path(self._test_root)

        data = parser.sequences

        test_output = list(parser.output())
        self.assertEqual(len(test_output), 1)
        self.assertEqual(test_output[0], final_output)

        # Check the structure of the sequences property.
        self.assertIn(self._test_root, data)
        self.assertEqual(len(data), 1)
        self.assertIn(self._test_file_name, data[self._test_root])
        self.assertEqual(len(data[self._test_root]), 1)

        # Now check the file sequence itself.
        file_seq = data[self._test_root][self._test_file_name]

        test_output = list(file_seq.output())

        self.assertEqual(len(test_output), 1)
        self.assertEqual(test_output[0], final_output)

        self.assertIn(self._test_ext, file_seq)
        self.assertEqual(len(file_seq), 1)
        self.assertTrue(4 in file_seq[self._test_ext])
        self.assertEqual(len(file_seq[self._test_ext]), 1)

        # And finally, the frame sequence.
        frame_seq = file_seq[self._test_ext][4]

        self.assertEqual(len(frame_seq), len(frames[4]))
        self.assertEqual(str(frame_seq), frame_seq_output)

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_simple_sequence(self, mock_api_call):
        """Test simple file sequence discovery from disk location."""
        frames = {4: [0, 1, 2, 3, 4]}

        # Expected outputs ...
        frame_seq_output = "0000-0004"
        file_seq_output = ".".join(
            (self._test_file_name, frame_seq_output, self._test_ext))
        final_output = os.path.join(self._test_root, file_seq_output)

        input_files = generate_files(
            ext=self._test_ext, frames=frames, name=self._test_file_name)

        mock_api_call.return_value = [(self._test_root, [], input_files)]

        parser = get_parser()
        parser.scan_path(self._test_root)

        data = parser.sequences

        test_output = list(parser.output())
        self.assertEqual(len(test_output), 1)
        self.assertEqual(test_output[0], final_output)

        # Check the structure of the sequences property.
        self.assertIn(self._test_root, data)
        self.assertEqual(len(data), 1)
        self.assertIn(self._test_file_name, data[self._test_root])
        self.assertEqual(len(data[self._test_root]), 1)

        # Now check the file sequence itself.
        file_seq = data[self._test_root][self._test_file_name]

        test_output = list(file_seq.output())

        self.assertEqual(len(test_output), 1)
        self.assertEqual(test_output[0], final_output)

        self.assertIn(self._test_ext, file_seq)
        self.assertEqual(len(file_seq), 1)
        self.assertTrue(4 in file_seq[self._test_ext])
        self.assertEqual(len(file_seq[self._test_ext]), 1)

        # And finally, the frame sequence.
        frame_seq = file_seq[self._test_ext][4]

        self.assertEqual(len(frame_seq), len(frames[4]))
        self.assertEqual(str(frame_seq), frame_seq_output)

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_complex_sequence(self, mock_api_call):
        """Test complex file sequence discovery from disk location."""
        frames = {
            1: [5, 6, 7, 8, 114, 199, 2000],
            3: [8, 9, 10, 12],
            4: [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 101]
        }

        input_files = generate_files(
            ext=self._test_ext, frames=frames, name=self._test_file_name)

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

        mock_api_call.return_value = [(self._test_root, [], input_files)]

        parser = get_parser()
        parser.scan_path(self._test_root)

        final_output = list()
        for pad, seq_frames in sorted(output_seqs.items()):
            bits = (self._test_file_name, seq_frames, self._test_ext)
            final_output.append(os.path.join(self._test_root, ".".join(bits)))

        data = parser.sequences

        # Check the structure of the sequences property.
        self.assertIn(self._test_root, data)
        self.assertEqual(len(data), 1)
        self.assertIn(self._test_file_name, data[self._test_root])
        self.assertEqual(len(data[self._test_root]), 1)

        # Now check the file sequence itself.
        file_seq = data[self._test_root][self._test_file_name]

        test_output = list(file_seq.output())
        self.assertEqual(len(test_output), 3)
        self.assertEqual(test_output, final_output)

        self.assertIn(self._test_ext, file_seq)
        self.assertEqual(len(file_seq), 1)
        self.assertEqual(set(file_seq[self._test_ext]), set(output_seqs))

        # And finally, the frame sequences.
        for pad in sorted(output_seqs):
            self.assertEqual(output_seqs[pad],
                             str(file_seq[self._test_ext][pad]))

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_nested_sequences(self, mock_api_call):
        """Test file sequence discovery in nested directories."""
        mock_api_call.side_effect = mock_walk_deep

        print "\n\n  SEQUENCES\n  ---------"
        parser = get_parser()
        parser.scan_path(self._test_root)
        for seq in parser.output():
            print " ", seq

        print "\n  LEVELS\n  ------"
        for level in xrange(0, 5):
            parser = get_parser()
            parser.scan_path(self._test_root, level=level)

            expected_seqs = level
            if level == 0:
                expected_seqs = 4

            seqs = list(parser.output())
            blurb = "  o level == %d: %d (%d expected) entries"
            print blurb % (level, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq
            self.assertEqual(len(seqs), expected_seqs)

        print

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

        print "\n\n  GOOD SEQUENCES\n  --------------"
        for frame_seq in good_frame_seqs:
            output = validate_frame_sequence(frame_seq)
            print '  o "%s" --> %s' % (frame_seq, output)
            self.assertTrue(output)

        print "\n  BAD SEQUENCES\n  -------------"
        for frame_seq in bad_frame_seqs:
            print '  o "%s"' % frame_seq
            self.assertFalse(validate_frame_sequence(frame_seq))

        print

    def test_add_file_sequence(self):
        """Test file sequence addition via seqparse.add_file."""
        input_file = ".".join((self._test_file_name, "0005", self._test_ext))
        input_file = os.path.join(self._test_root, input_file)

        # Expected outputs ...
        input_frame_seq = "0000-0004"
        output_frame_seq = "0000-0005"
        input_file_seq = ".".join(
            (self._test_file_name, input_frame_seq, self._test_ext))
        input_file_seq = os.path.join(self._test_root, input_file_seq)
        output_file_seq = ".".join(
            (self._test_file_name, output_frame_seq, self._test_ext))
        output_file_seq = os.path.join(self._test_root, output_file_seq)

        print "\n\n  INPUT FILES\n  -----------"
        print "  o", input_file_seq
        print "  o", input_file

        parser = get_parser()
        parser.add_file(input_file_seq)
        parser.add_file(input_file)

        output = list(parser.output())

        print "\n  OUTPUT FILES\n  ------------"
        for line in output:
            print "  o", line

        print "\n  EXPECTED OUTPUT\n  ---------------"
        print "  o", output_file_seq
        print

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], output_file_seq)
