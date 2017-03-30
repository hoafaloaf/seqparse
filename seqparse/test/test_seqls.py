"""Tests for the seqls script (seqparse.cli.seqls)."""

# Standard Libraries
import copy
import os
import shlex
import unittest

# Third Party Libraries
import mock

from . import (DirEntry, generate_entries, initialise_mock_scandir_data,
               mock_scandir_deep)
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
            all=False,
            human_readable=False,
            long_format=False,
            max_levels=[-1],
            min_levels=[-1],
            missing=False,
            search_path=["."],
            seqs_only=False)
        args = vars(seqls.parse_args([]))
        self.assertEqual(args, defaults)

        # yapf: disable
        data = [
            (["-laH"], dict(all=True, human_readable=True, long_format=True)),
            (shlex.split("test_dir -l"), dict(
                search_path=["test_dir"], long_format=True)),
            (shlex.split("--maxdepth 0"), dict(max_levels=[0])),
            (["test_dir"], dict(search_path=["test_dir"])),
            (shlex.split("--maxdepth 0 --mindepth 2"), dict(
                max_levels=[0], min_levels=[2])),
            (shlex.split("--maxdepth 1 -S"), dict(
                max_levels=[1], seqs_only=True)),
            (shlex.split("-m test_dir"), dict(
                missing=True, search_path=["test_dir"]))]
        # yapf: enable

        for input_args, updated_options in data:
            expected_options = copy.deepcopy(defaults)
            expected_options.update(updated_options)
            self.assertEqual(expected_options,
                             vars(seqls.parse_args(input_args)))

    @mock.patch("seqparse.seqparse.scandir")
    def test_seqls_with_arguments(self, mock_api_call):
        """Seqls: Test seqls with supplied arguments."""
        mock_api_call.side_effect = mock_scandir_deep

        print "\n  SEQUENCES\n  ---------"
        initialise_mock_scandir_data(
            os.path.join(os.getcwd(), self._test_root))
        args = seqls.parse_args(["test_dir"])
        seqs = list(seqls.main(args, _debug=True))
        for seq in seqs:
            print " ", seq

        print "\n  MAX LEVELS\n  ----------"
        for max_levels in xrange(-1, 4):
            initialise_mock_scandir_data(
                os.path.join(os.getcwd(), self._test_root))
            args = seqls.parse_args(
                shlex.split("test_dir --maxdepth {:d}".format(max_levels)))
            seqs = list(seqls.main(args, _debug=True))

            expected_seqs = max_levels + 2
            if max_levels == -1:
                expected_seqs = 5

            blurb = "  o max_levels == {:d}: {:d} ({:d} expected) entries"
            print blurb.format(max_levels, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq
            self.assertEqual(len(seqs), expected_seqs)

        print "\n  MIN LEVELS\n  ----------"
        for min_levels in xrange(-1, 4):
            initialise_mock_scandir_data(
                os.path.join(os.getcwd(), self._test_root))
            args = seqls.parse_args(
                shlex.split("test_dir --mindepth {:d}".format(min_levels)))
            seqs = list(seqls.main(args, _debug=True))

            expected_seqs = 3 - min_levels
            if min_levels == -1:
                expected_seqs = 5

            blurb = "  o min_levels == {:d}: {:d} ({:d} expected) entries"
            print blurb.format(min_levels, len(seqs), expected_seqs)

            for seq in seqs:
                print "    -", seq
            self.assertEqual(len(seqs), expected_seqs)

        print

    @mock.patch("seqparse.seqparse.scandir")
    def test_singletons(self, mock_api_call):
        """Seqls: Test file singleton discovery from disk location."""
        output = [os.path.join(self._test_root, x) for x in self._singletons]

        entries = list()
        for file_name in output:
            entries.append(DirEntry(file_name))

        mock_api_call.return_value = iter(entries)

        args = seqls.parse_args(["test_dir"])
        file_names = list(seqls.main(args, _debug=True))
        self.assertEqual(sorted(file_names), output)

        # Test seqs_only option ...
        args = seqls.parse_args(["test_dir", "-S"])
        file_names = list(seqls.main(args, _debug=True))
        self.assertEqual(file_names, [])

    @mock.patch("seqparse.seqparse.scandir")
    def test_missing(self, mock_api_call):
        """Seqls: Test missing option."""
        file_path = os.path.join(self._test_root, self._test_file_name)

        chunk_in = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in)

        input_entries = map(DirEntry, fseq)

        mock_api_call.return_value = iter(input_entries)

        chunk_out = FrameChunk(first=2, last=10, step=2, pad=4)
        expected = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_out)

        args = seqls.parse_args(["test_dir", "-m"])
        inverted = seqls.main(args, _debug=True)

        self.assertEqual(len(inverted), 1)

        print "\n\n  SEQUENCE\n  --------"
        print "  input files:   ", fseq
        print "  expected files:", expected
        print "  inverted files:", inverted[0]

        self.assertEqual(inverted[0], str(expected))

    @mock.patch("seqparse.seqparse.scandir")
    def test_long_format(self, mock_api_call):
        """Seqls: Test the long-format option."""
        frames = {4: (1, 2, 3, 4, 6)}
        root_dir = os.path.join(os.getcwd(), self._test_root)
        input_entries = generate_entries(
            name="test", ext="py", frames=frames, root=root_dir)

        mock_api_call.return_value = iter(input_entries)

        args = seqls.parse_args(["test_dir", "-l"])
        output = seqls.main(args, _debug=True)
        expected = "35.7K  2017/03/30 14:11  {}/test.0001-0004,0006.py"

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], expected.format(root_dir))

        args = seqls.parse_args(["test_dir", "-l", "-m"])
        output = seqls.main(args, _debug=True)

        self.assertEqual(len(output), 0)
