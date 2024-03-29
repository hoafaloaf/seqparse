"""Tests for the seqls script (seqparse.cli.seqls)."""

import copy
import os
import shlex
import time
import unittest
from unittest import mock

from . import (DirEntry, generate_entries, initialise_mock_scandir_data,
               mock_scandir_deep)
from .. import get_version
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

    def test_parse_args(self):
        """Seqls: Test seqls argument parsing."""
        defaults = dict(all=False,
                        human_readable=False,
                        long_format=False,
                        max_levels=[-1],
                        min_levels=[-1],
                        missing=False,
                        search_path=["."],
                        seqs_only=False,
                        version=False)
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
                missing=True, search_path=["test_dir"], seqs_only=True))]
        # yapf: enable

        for input_args, updated_options in data:
            expected_options = copy.deepcopy(defaults)
            expected_options.update(updated_options)
            self.assertEqual(expected_options,
                             vars(seqls.parse_args(input_args)))

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_seqls_with_arguments(self, mock_api_call):
        """Seqls: Test seqls with supplied arguments."""
        mock_api_call.side_effect = mock_scandir_deep

        args = seqls.parse_args(["--version"])
        version = seqls.main(args, _debug=True)
        self.assertEqual(version, get_version(pretty=True))

        print("\n  SEQUENCES\n  ---------")
        initialise_mock_scandir_data(os.path.join(os.getcwd(),
                                                  self._test_root))
        args = seqls.parse_args(["test_dir"])
        seqs = list(seqls.main(args, _debug=True))
        for seq in seqs:
            print(" ", seq)

        print("\n  MAX LEVELS\n  ----------")
        for max_levels in range(-1, 4):
            initialise_mock_scandir_data(
                os.path.join(os.getcwd(), self._test_root))
            args = seqls.parse_args(
                shlex.split(f'test_dir --maxdepth {max_levels:d}'))
            seqs = list(seqls.main(args, _debug=True))

            expected_seqs = max_levels + 2
            if max_levels == -1:
                expected_seqs = 5

            blurb = "  o max_levels == {:d}: {:d} ({:d} expected) entries"
            print(blurb.format(max_levels, len(seqs), expected_seqs))

            for seq in seqs:
                print("    -", seq)
            self.assertEqual(len(seqs), expected_seqs)

        print("\n  MIN LEVELS\n  ----------")
        for min_levels in range(-1, 4):
            initialise_mock_scandir_data(
                os.path.join(os.getcwd(), self._test_root))
            args = seqls.parse_args(
                shlex.split(f'test_dir --mindepth {min_levels:d}'))
            seqs = list(seqls.main(args, _debug=True))

            expected_seqs = 3 - min_levels
            if min_levels == -1:
                expected_seqs = 5

            blurb = "  o min_levels == {:d}: {:d} ({:d} expected) entries"
            print(blurb.format(min_levels, len(seqs), expected_seqs))

            for seq in seqs:
                print("    -", seq)
            self.assertEqual(len(seqs), expected_seqs)

        print("")

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_singletons(self, mock_api_call):
        """Seqls: Test file singleton discovery from disk location."""
        output = [os.path.join(self._test_root, x) for x in self._singletons]

        entries = []
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

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_missing_option(self, mock_api_call):
        """Seqls: Test missing option."""
        file_path = os.path.join(self._test_root, self._test_file_name)

        chunk_in = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(name=file_path,
                            ext=self._test_ext,
                            frames=chunk_in)

        input_entries = list(map(DirEntry, fseq))

        mock_api_call.return_value = iter(input_entries)

        chunk_out = FrameChunk(first=2, last=10, step=2, pad=4)
        expected = FileSequence(name=file_path,
                                ext=self._test_ext,
                                frames=chunk_out)

        args = seqls.parse_args(["test_dir", "-m"])
        inverted = seqls.main(args, _debug=True)

        self.assertEqual(len(inverted), 1)

        print("\n\n  SEQUENCE\n  --------")
        print("  input files:   ", fseq)
        print("  expected files:", expected)
        print("  inverted files:", inverted[0])

        self.assertEqual(inverted[0], str(expected))

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_long_format_option(self, mock_api_call):
        """Seqls: Test the long-format option."""
        frames = {4: (1, 2, 3, 4, 6)}
        root_dir = os.path.join(os.getcwd(), self._test_root)
        input_entries = generate_entries(name="test",
                                         ext="py",
                                         frames=frames,
                                         root=root_dir)

        input_entries.extend(
            generate_entries(name=".test",
                             ext="py",
                             frames=frames,
                             root=self._test_root))

        input_entries.append(DirEntry(os.path.join(root_dir, "pony.py")))

        file_date = time.strftime('%Y/%m/%d %H:%M', time.localtime(1490997828))
        fseq_date = time.strftime('%Y/%m/%d %H:%M', time.localtime(1490908305))
        opts = dict(file_date=file_date, fseq_date=fseq_date, root=root_dir)

        mock_api_call.return_value = input_entries

        args = seqls.parse_args(["test_dir", "-l"])
        output = seqls.main(args, _debug=True)
        expected = [
            "36520  {fseq_date}  {root}/test.0001-0004,0006.py",
            "9436   {file_date}  {root}/pony.py"
        ]
        expected = [x.replace("/", os.sep).format(**opts) for x in expected]

        self.assertEqual(len(output), 2)
        self.assertEqual(output, expected)

        args = seqls.parse_args(["test_dir", "-l", "-H"])
        output = seqls.main(args, _debug=True)
        expected = [
            "35.7K  {fseq_date}  {root}/test.0001-0004,0006.py",
            "9.2K   {file_date}  {root}/pony.py"
        ]
        expected = [x.replace("/", os.sep).format(**opts) for x in expected]

        self.assertEqual(len(output), 2)
        self.assertEqual(output, expected)

        args = seqls.parse_args(["test_dir", "-l", "-m"])
        output = seqls.main(args, _debug=True)

        fseq_date = time.strftime('%Y/%m/%d %H:%M', time.localtime(None))
        opts = dict(fseq_date=fseq_date, root=root_dir)

        expected = ["----  {fseq_date}  {root}/test.0005.py"]
        expected = [x.replace("/", os.sep).format(**opts) for x in expected]

        self.assertEqual(len(output), 1)
        self.assertEqual(output, expected)

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_all_option(self, mock_api_call):
        """Seqls: Test the all option."""
        frames = {4: (1, 2, 3, 4, 6)}
        root_dir = os.path.join(os.getcwd(), self._test_root)

        input_entries = generate_entries(name="test",
                                         ext="py",
                                         frames=frames,
                                         root=root_dir)

        input_entries.extend(
            generate_entries(name=".test",
                             ext="py",
                             frames=frames,
                             root=root_dir))

        mock_api_call.return_value = input_entries

        args = seqls.parse_args(["test_dir"])
        output = seqls.main(args, _debug=True)

        expected = [
            os.path.join(root_dir, ".test.0001-0004,0006.py"),
            os.path.join(root_dir, "test.0001-0004,0006.py")
        ]

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], expected[1])

        args = seqls.parse_args(["test_dir", "-a"])
        output = seqls.main(args, _debug=True)

        self.assertEqual(len(output), 2)
        self.assertEqual(output, expected)
