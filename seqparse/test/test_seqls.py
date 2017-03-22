"""Tests for the seqls script (seqparse.cli.seqls)."""

# Standard Libraries
import copy
import os
import unittest

# Third Party Libraries
import mock

from . import mock_walk_deep
from ..cli import seqls


###############################################################################
# class: TestFrameSequences


class TestSeqls(unittest.TestCase):
    """Test basic functionality on the seqls script."""

    _test_ext = "exr"
    _test_file_name = "TEST_DIR"
    _test_root = "test_dir"
    _singletons = ["singleton0.jpg", "singleton1.jpg"]

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_parse_args(self):
        """Seqls: Test seqls argument parsing."""
        defaults = dict(level=["0"], search_path=["."], seqs_only=False)
        args = vars(seqls.parse_args([]))
        self.assertEqual(args, defaults)

        data = [
            (["-l", "1"], dict(level=["1"])),
            (["test_dir"], dict(search_path=["test_dir"])),
            (["-l", "1", "test_dir"], dict(
                level=["1"], search_path=["test_dir"])),
            (["-l", "1", "test_dir", "-S"], dict(
                level=["1"], search_path=["test_dir"], seqs_only=True)),
        ]

        for input_args, updated_options in data:
            expected_options = copy.deepcopy(defaults)
            expected_options.update(updated_options)
            self.assertEqual(expected_options,
                             vars(seqls.parse_args(input_args)))

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_seqls_with_arguments(self, mock_api_call):
        """Seqls: Test seqls with supplied arguments."""
        mock_api_call.side_effect = mock_walk_deep

        print "\n  SEQUENCES\n  ---------"
        args = seqls.parse_args(["test_dir"])
        seqs = list(seqls.main(args, _debug=True))
        for seq in seqs:
            print " ", seq

        print "\n  LEVELS\n  ------"
        for level in xrange(0, 5):
            expected_seqs = level + 1
            if level == 0:
                expected_seqs = 5

            # Mimicking argparse output (everything's a string)
            level = str(level)

            args = seqls.parse_args(["test_dir", "-l", level])
            seqs = list(seqls.main(args, _debug=True))
            blurb = "  o level == %s: %d entries (%d expected)"
            print blurb % (level, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq

            self.assertEqual(len(seqs), expected_seqs)

        print

    @mock.patch("seqparse.seqparse.scandir.walk")
    def test_singletons(self, mock_api_call):
        """Seqls: Test file singleton discovery from disk location."""
        mock_api_call.return_value = [(self._test_root, [], self._singletons)]

        # Expected outputs ...
        output = [os.path.join(self._test_root, x) for x in self._singletons]

        args = seqls.parse_args(["test_dir"])
        file_names = list(seqls.main(args, _debug=True))
        self.assertEqual(sorted(file_names), output)

        # Test seqs_only option ...
        args = seqls.parse_args(["test_dir", "-S"])
        file_names = list(seqls.main(args, _debug=True))
        self.assertEqual(file_names, [])
