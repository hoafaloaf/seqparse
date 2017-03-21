"""Test the regex module."""

# Standard Libraries
import unittest

from seqparse.regex import SeqparseRegexMixin

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
        """Test the bits_match method."""
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

        print "\n\n  GOOD CHUNKS\n  -----------"
        for chunk, result in good_chunks:
            bits_dict = self.regex.bits_match(chunk, as_dict=True)
            print '  o "%s" --> %s' % (chunk, bits_dict)
            self.assertEqual(bits_dict, result)

            result_tuple = tuple(bits_dict[x]
                                 for x in ("first", "last", "step"))
            self.assertEqual(self.regex.bits_match(chunk), result_tuple)

        print "\n  BAD SEQUENCES\n  -------------"
        for chunk in bad_chunks:
            print '  o "%s"' % chunk
            self.assertFalse(self.regex.bits_match(chunk))

        print
