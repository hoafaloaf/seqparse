"""Tests for the seqls script (seqparse.cli.seqls)."""

# Standard Libraries
import unittest

# Third Party Libraries
import mock

from . import mock_walk_deep
from ..cli import seqls


###############################################################################
# class: TestFrameSequences


class TestSeqls(unittest.TestCase):
    """Test basic functionality on the seqls script."""

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_parse_args(self):
        """Test seqls argument parsing."""
        args = vars(seqls.parse_args([]))
        self.assertEqual(args, dict(level=["0"], search_path=["."]))
        args = vars(seqls.parse_args(["-l", "1"]))
        self.assertEqual(args, dict(level=["1"], search_path=["."]))
        args = vars(seqls.parse_args(["test_dir"]))
        self.assertEqual(args, dict(level=["0"], search_path=["test_dir"]))
        args = vars(seqls.parse_args(["-l", "1", "test_dir"]))
        self.assertEqual(args, dict(level=["1"], search_path=["test_dir"]))
        args = vars(seqls.parse_args(["test_dir", "-l", "1"]))
        self.assertEqual(args, dict(level=["1"], search_path=["test_dir"]))

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_seqls_with_arguments(self, mock_api_call):
        """Test seqls with supplied arguments."""
        mock_api_call.side_effect = mock_walk_deep

        print "\n  SEQUENCES\n  ---------"
        seqs = list(seqls.main("test_dir", _debug=True))
        for seq in seqs:
            print " ", seq

        print "\n  LEVELS\n  ------"
        for level in xrange(0, 5):
            expected_seqs = level
            if level == 0:
                expected_seqs = 4

            # Mimicking argparse output (everything's a string)
            level = str(level)

            seqs = list(
                seqls.main(
                    search_path=["test_dir"], level=[level], _debug=True))
            blurb = "  o level == %s: %d entries (%d expected)"
            print blurb % (level, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq

            self.assertEqual(len(seqs), expected_seqs)

        print
