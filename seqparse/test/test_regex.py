"""Test the regex module."""

# "Future" Libraries
from __future__ import print_function

# Standard Libraries
import unittest

from ..regex import SeqparseRegexMixin

###############################################################################
# class: TestRegex


class TestSeqparseModule(unittest.TestCase):
    """Test the regex module."""

    _test_ext = "exr"
    _test_file_name = "TEST_DIR"
    _test_root = "test_dir"
    _singletons = ["singleton0.jpg", "singleton1.jpg"]

    def setUp(self):
        """Set up the test case."""
        self.regex = SeqparseRegexMixin()

    def test_bits_match(self):
        """SeqparseRegexMixin: Test the bits_match method."""
        good_chunks = [
            ("0001", dict(first="0001", last=None, step=None)),
            ("001-002", dict(first="001", last="002", step=None)),
            ("1-2", dict(first="1", last="2", step=None)),
            ("1-10", dict(first="1", last="10", step=None)),
            ("0001-0010x2", dict(first="0001", last="0010", step="2")),
            ("001-101x2", dict(first="001", last="101", step="2")),
            ("1-11x2", dict(first="1", last="11", step="2"))
        ]
        bad_chunks = ["-0001", "0001-", "0001x2", "x2"]

        print("\n\n  GOOD CHUNKS\n  -----------")
        for chunk, result in good_chunks:
            bits_dict = self.regex.bits_match(chunk, as_dict=True)
            print('  o "{}" --> {}'.format(chunk, bits_dict))
            self.assertEqual(bits_dict, result)

            result_tuple = tuple(bits_dict[x]
                                 for x in ("first", "last", "step"))
            self.assertEqual(self.regex.bits_match(chunk), result_tuple)

        print("\n  BAD SEQUENCES\n  -------------")
        for chunk in bad_chunks:
            print('  o "{}"'.format(chunk))
            self.assertIsNone(self.regex.bits_match(chunk))

        print("")

    def test_file_name_match(self):
        """SeqparseRegexMixin: Test the file_name_match method."""
        good_names = [
            ("0001.exr", dict(name=None, frame="0001", ext="exr")),
            ("kitty.1.jpg", dict(name="kitty", frame="1", ext="jpg")), (
                "/i/like/cats/kitty.0001.tif",
                dict(name="/i/like/cats/kitty", frame="0001", ext="tif"))
        ]
        bad_names = ["kitty.0001", "1", ".111", "111.", ".22.tif"]
        bad_names.extend(self._singletons)

        print("\n\n  GOOD NAMES\n  ----------")
        for file_name, result in good_names:
            bits_dict = self.regex.file_name_match(file_name, as_dict=True)
            print('  o "{}" --> {}'.format(file_name, bits_dict))
            self.assertEqual(bits_dict, result)

            result_tuple = tuple(bits_dict[x]
                                 for x in ("name", "frame", "ext"))
            self.assertEqual(
                self.regex.file_name_match(file_name), result_tuple)

        print("\n  BAD SEQUENCES\n  -------------")
        for file_name in bad_names:
            print('  o "{}"'.format(file_name))
            self.assertIsNone(self.regex.file_name_match(file_name))

        print("")

    def test_file_seq_match(self):
        """SeqparseRegexMixin: Test the file_seq_match method."""
        good_names = [
            ("0001-0011.exr", dict(name=None, frames="0001-0011", ext="exr")),
            ("kitty.1,3,9.jpg", dict(name="kitty", frames="1,3,9", ext="jpg")),
            ("/i/like/cats/kitty.11,22-33.tif",
             dict(name="/i/like/cats/kitty", frames="11,22-33", ext="tif"))
        ]
        bad_names = ["kitty.0001-0011", "1,3,9", ".111", "111.", ".22.tif"]
        bad_names.extend(self._singletons)

        print("\n\n  GOOD NAMES\n  ----------")
        for frame_seq, result in good_names:
            bits_dict = self.regex.file_seq_match(frame_seq, as_dict=True)
            print('  o "{}" --> {}'.format(frame_seq, bits_dict))
            self.assertEqual(bits_dict, result)

            result_tuple = tuple(bits_dict[x]
                                 for x in ("name", "frames", "ext"))
            self.assertEqual(
                self.regex.file_seq_match(frame_seq), result_tuple)

        print("\n  BAD SEQUENCES\n  -------------")
        for frame_seq in bad_names:
            print('  o "{}"'.format(frame_seq))
            bits_dict = self.regex.bits_match(frame_seq, as_dict=True)
            self.assertIsNone(self.regex.file_seq_match(frame_seq))

        print("")

    def test_is_frame_sequence(self):
        """SeqparseRegexMixin: Test the is_file_sequence method."""
        good_frame_seqs = [
            "0001", ",0001", "0001,", "0001-0001", "0001-0001x0",
            "0001-0003x3", "0001,0003", "0001,,0003", "0001-0010",
            "0001-0010x0", "0001-0011x2", "0001-0012x2", "0001-0005,0007-0010",
            "0001-0005x2,0007-0010", "0001-0005,0007-0011x2",
            "0001-0005,0006,0008-0012x2", "0001,0003-0007,0009-0015x2"
        ]
        bad_frame_seqs = [
            "-0001", "0001-", "0001x2", "x2", "0001,0003x2", "0001-0005x", "x",
            ",", ",,", ""
        ]

        print("\n\n  GOOD SEQUENCES\n  --------------")
        for frame_seq in good_frame_seqs:
            print('  o "{}"'.format(frame_seq))
            self.assertTrue(self.regex.is_frame_sequence(frame_seq))

        print("\n  BAD SEQUENCES\n  -------------")
        for frame_seq in bad_frame_seqs:
            print('  o "{}"'.format(frame_seq))
            self.assertFalse(self.regex.is_frame_sequence(frame_seq))

        print("")
