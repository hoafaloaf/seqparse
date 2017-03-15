"""Tests for the seqls script (seqparse.cli.seqls)."""

# Standard Libraries
import os
import sys
import unittest

# Third Party Libraries
import mock

from . import generate_files
from ..cli import seqls


def mock_walk(search_path="."):
    """A mocked version of scandir.walk for testing purposes."""
    frames = {4: [0, 1, 2, 3, 4]}
    level1_path = os.path.join(search_path, "level1")
    level2_path = os.path.join(level1_path, "level2")
    level3_path = os.path.join(level2_path, "level3")

    level0_files = generate_files(ext="exr", frames=frames, name="level0")
    level1_files = generate_files(ext="exr", frames=frames, name="level1")
    level2_files = generate_files(ext="exr", frames=frames, name="level2")
    level3_files = generate_files(ext="exr", frames=frames, name="level3")

    return_value = [(search_path, ["level1"], level0_files),
                    (level1_path, ["level2"], level1_files),
                    (level2_path, ["level3"], level2_files),
                    (level3_path, [], level3_files)]

    dir_names = list()
    for index, entry in enumerate(return_value):
        if index and not dir_names:
            raise StopIteration

        del dir_names[:]
        dir_names.extend(entry[1])
        root, file_names = entry[0], entry[2]
        yield root, dir_names, file_names


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

    @mock.patch("seqparse.seqparse.scandir.walk", side_effect=mock_walk)
    def test_seqls_with_arguments(self, mock_walk):
        """Test seqls with supplied arguments."""
        print "\n  SEQUENCES\n  ---------"
        seqs = list(seqls.main("test_dir", _debug=True))
        for seq in seqs:
            print " ", seq

        print "\n  LEVELS\n  ------"
        for level in xrange(0, 5):
            expected_seqs = level
            if level == 0:
                expected_seqs = 4

            seqs = list(
                seqls.main(search_path="test_dir", level=level, _debug=True))
            blurb = "  o level == %d: %d entries (%d expected)"
            print blurb % (level, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq

            self.assertEqual(len(seqs), expected_seqs)
