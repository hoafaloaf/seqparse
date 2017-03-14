"""Tests for the seqls script (seqparse.cli.seqls)."""

# Standard Libraries
import sys
import unittest

# Third Party Libraries
import mock

from seqparse.cli import seqls

###############################################################################
# class: TestFrameSequences


class TestSeqls(unittest.TestCase):
    """Test basic functionality on the seqls script."""

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_argparse(self):
        """Test seqls without any command line arguments."""
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
