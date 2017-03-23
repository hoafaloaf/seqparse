"""Tests for the seqls script (seqparse.cli.seqls)."""

# Standard Libraries
import copy
import os
import unittest

# Third Party Libraries
import mock

from . import mock_walk_deep
from ..cli import seqls
from ..sequences import FileSequence, FrameChunk

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
        defaults = dict(
            max_levels=[-1],
            min_levels=[-1],
            missing=False,
            search_path=["."],
            seqs_only=False)
        args = vars(seqls.parse_args([]))
        self.assertEqual(args, defaults)

        data = [
            (["--maxdepth", "0"], dict(max_levels=[0])),
            (["test_dir"], dict(search_path=["test_dir"])), (
                ["--maxdepth", "0", "--mindepth", "2"], dict(
                    max_levels=[0],
                    min_levels=[2])), (["--maxdepth", "1", "-S"], dict(
                        max_levels=[1], seqs_only=True)),
            (["-m", "test_dir"], dict(missing=True, search_path=["test_dir"]))
        ]

        for input_args, updated_options in data:
            expected_options = copy.deepcopy(defaults)
            expected_options.update(updated_options)
            self.assertEqual(expected_options,
                             vars(seqls.parse_args(input_args)))

    @mock.patch("seqparse.seqparse.walk")
    def test_seqls_with_arguments(self, mock_api_call):
        """Seqls: Test seqls with supplied arguments."""
        mock_api_call.side_effect = mock_walk_deep

        print "\n  SEQUENCES\n  ---------"
        args = seqls.parse_args(["test_dir"])
        seqs = list(seqls.main(args, _debug=True))
        for seq in seqs:
            print " ", seq

        print "\n  LEVELS\n  ------"
        for max_levels in xrange(-1, 4):
            expected_seqs = max_levels + 2
            if max_levels == -1:
                expected_seqs = 5

            # Mimicking argparse output (everything's a string)
            max_levels = str(max_levels)

            args = seqls.parse_args(["test_dir", "--maxdepth", max_levels])
            seqs = list(seqls.main(args, _debug=True))
            blurb = "  o max_levels == %s: %d entries (%d expected)"
            print blurb % (max_levels, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq

            self.assertEqual(len(seqs), expected_seqs)

        print

    @mock.patch("seqparse.seqparse.walk")
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

    @mock.patch("seqparse.seqparse.walk")
    def test_missing(self, mock_api_call):
        """Seqls: Test missing option."""
        file_path = os.path.join(self._test_root, self._test_file_name)

        chunk_in = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in)

        input_files = list(fseq)

        mock_api_call.return_value = [("", [], input_files)]

        chunk_out = FrameChunk(first=2, last=10, step=2, pad=4)
        expected = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_out)

        args = seqls.parse_args(["test_dir"])
        inverted = seqls.main(args, _debug=True)

        self.assertEqual(len(inverted), 1)
        self.assertEqual(inverted[0], str(fseq))

        args = seqls.parse_args(["test_dir", "-m"])
        inverted = seqls.main(args, _debug=True)

        self.assertEqual(len(inverted), 1)
        self.assertEqual(inverted[0], str(expected))
