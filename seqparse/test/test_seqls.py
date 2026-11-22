"""Tests for the seqls script (seqparse.cli.seqls)."""

import contextlib
import copy
import io
import json
import os
import shlex
import tempfile
import time
import unittest
from unittest import mock

import seqparse
from seqparse import sequences, test
from seqparse.cli import seqls
from seqparse.test import test_windows_paths

###############################################################################
# class: TestFrameSequences


class TestSeqls(unittest.TestCase):
    """Test basic functionality on the seqls script."""

    _test_ext = "exr"
    _test_file_name = "TEST_DIR"
    _test_root = "test_dir"
    _singletons = ("singleton0.jpg", "singleton1.jpg")

    def test_parse_args(self):
        """Seqls: Test seqls argument parsing."""
        defaults = {
            "all": False,
            "human_readable": False,
            "json": False,
            "long_format": False,
            "max_levels": [-1],
            "min_levels": [-1],
            "missing": False,
            "search_path": ["."],
            "seqs_only": False,
            "version": False,
        }
        args = vars(seqls.parse_args([]))
        self.assertEqual(args, defaults)

        # fmt: off
        data = [
            (["-laH"], {
                "all": True, "human_readable": True, "long_format": True}),
            (shlex.split("test_dir -l"), {
                "search_path": ["test_dir"], "long_format": True}),
            (shlex.split("--maxdepth 0"), {"max_levels": [0]}),
            (["test_dir"], {"search_path": ["test_dir"]}),
            (shlex.split("--maxdepth 0 --mindepth 2"), {
                "max_levels": [0], "min_levels": [2]}),
            (shlex.split("--maxdepth 1 -S"), {
                "max_levels": [1], "seqs_only": True}),
            (shlex.split("-m test_dir"), {
                "missing": True, "search_path": ["test_dir"],
                "seqs_only": True})]
        # fmt: on

        for input_args, updated_options in data:
            expected_options = copy.deepcopy(defaults)
            expected_options.update(updated_options)
            self.assertEqual(
                expected_options, vars(seqls.parse_args(input_args))
            )

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_seqls_with_arguments(self, mock_api_call):
        """Seqls: Test seqls with supplied arguments."""
        mock_api_call.side_effect = test.mock_scandir_deep

        args = seqls.parse_args(["--version"])
        version = seqls.main(args, _debug=True)
        self.assertEqual(version, seqparse.get_version(pretty=True))

        print("\n  SEQUENCES\n  ---------")
        test.initialise_mock_scandir_data(
            os.path.join(os.getcwd(), self._test_root)
        )
        args = seqls.parse_args(["test_dir"])
        seqs = list(seqls.main(args, _debug=True))
        for seq in seqs:
            print(" ", seq)

        print("\n  MAX LEVELS\n  ----------")
        for max_levels in range(-1, 4):
            test.initialise_mock_scandir_data(
                os.path.join(os.getcwd(), self._test_root)
            )
            args = seqls.parse_args(
                shlex.split(f"test_dir --maxdepth {max_levels:d}")
            )
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
            test.initialise_mock_scandir_data(
                os.path.join(os.getcwd(), self._test_root)
            )
            args = seqls.parse_args(
                shlex.split(f"test_dir --mindepth {min_levels:d}")
            )
            seqs = list(seqls.main(args, _debug=True))

            # Level 0 holds two sequences, each deeper level holds one.
            expected_seqs = 4 - min_levels
            if min_levels < 1:
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
            entries.append(test.DirEntry(file_name))

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

        chunk_in = sequences.FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in
        )

        input_entries = list(map(test.DirEntry, fseq))

        mock_api_call.return_value = iter(input_entries)

        chunk_out = sequences.FrameChunk(first=2, last=10, step=2, pad=4)
        expected = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_out
        )

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
        input_entries = test.generate_entries(
            name="test", ext="py", frames=frames, root=root_dir
        )

        input_entries.extend(
            test.generate_entries(
                name=".test", ext="py", frames=frames, root=self._test_root
            )
        )

        input_entries.append(test.DirEntry(os.path.join(root_dir, "pony.py")))

        file_date = time.strftime("%Y/%m/%d %H:%M", time.localtime(1490997828))
        fseq_date = time.strftime("%Y/%m/%d %H:%M", time.localtime(1490908305))
        opts = {
            "file_date": file_date,
            "fseq_date": fseq_date,
            "root": root_dir,
        }

        mock_api_call.return_value = input_entries

        args = seqls.parse_args(["test_dir", "-l"])
        output = seqls.main(args, _debug=True)
        expected = [
            "36520  {fseq_date}  {root}/test.0001-0004,0006.py",
            "9436   {file_date}  {root}/pony.py",
        ]
        expected = [x.replace("/", os.sep).format(**opts) for x in expected]

        self.assertEqual(len(output), 2)
        self.assertEqual(output, expected)

        args = seqls.parse_args(["test_dir", "-l", "-H"])
        output = seqls.main(args, _debug=True)
        expected = [
            "35.7K  {fseq_date}  {root}/test.0001-0004,0006.py",
            "9.2K   {file_date}  {root}/pony.py",
        ]
        expected = [x.replace("/", os.sep).format(**opts) for x in expected]

        self.assertEqual(len(output), 2)
        self.assertEqual(output, expected)

        args = seqls.parse_args(["test_dir", "-l", "-m"])
        output = seqls.main(args, _debug=True)

        # Missing files have no disk stats: no size, no modification time.
        opts = {"root": root_dir}

        expected = ["----  ----  {root}/test.0005.py"]
        expected = [x.replace("/", os.sep).format(**opts) for x in expected]

        self.assertEqual(len(output), 1)
        self.assertEqual(output, expected)

    @mock.patch("seqparse.seqparse.os.scandir")
    def test_all_option(self, mock_api_call):
        """Seqls: Test the all option."""
        frames = {4: (1, 2, 3, 4, 6)}
        root_dir = os.path.join(os.getcwd(), self._test_root)

        input_entries = test.generate_entries(
            name="test", ext="py", frames=frames, root=root_dir
        )

        input_entries.extend(
            test.generate_entries(
                name=".test", ext="py", frames=frames, root=root_dir
            )
        )

        mock_api_call.return_value = input_entries

        args = seqls.parse_args(["test_dir"])
        output = seqls.main(args, _debug=True)

        expected = [
            os.path.join(root_dir, ".test.0001-0004,0006.py"),
            os.path.join(root_dir, "test.0001-0004,0006.py"),
        ]

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], expected[1])

        args = seqls.parse_args(["test_dir", "-a"])
        output = seqls.main(args, _debug=True)

        self.assertEqual(len(output), 2)
        self.assertEqual(output, expected)


###############################################################################
# Tests that scan real files


class _RealFilesTestCase(unittest.TestCase):
    """Base class: a temporary directory to fill with real files."""

    def setUp(self):
        """Create the temporary directory."""
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def touch(self, *names, size=0):
        """Create files of the given size in the temporary directory."""
        for name in names:
            with open(os.path.join(self.root, name), "w") as handle:
                handle.write("x" * size)

    def run_seqls(self, *options):
        """Run seqls on the temporary directory; return its text result."""
        args = seqls.parse_args([*options, self.root])
        return seqls.main(args, _debug=True)


class TestJsonOption(_RealFilesTestCase):
    """seqls --json."""

    def setUp(self):
        """Two sequences (one with a gap) and a singleton."""
        super().setUp()
        self.touch("plate.0001.exr", "plate.0002.exr", "plate.0004.exr", size=5)
        self.touch("comp.0001.png", "comp.0002.png", size=7)
        self.touch("notes.txt", size=3)

    def records(self, *options):
        """The parsed JSON records, keyed by name."""
        return {r["name"]: r for r in json.loads(self.run_seqls(*options))}

    def test_describes_sequences_and_files(self):
        """Every field of a sequence and of a singleton."""
        records = self.records("--json")
        self.assertEqual(set(records), {"plate", "comp", "notes.txt"})
        self.assertEqual(
            records["plate"],
            {
                "type": "sequence",
                "path": self.root,
                "name": "plate",
                "ext": "exr",
                "pad": 4,
                "frames": "0001,0002,0004",
                "count": 3,
                "first": 1,
                "last": 4,
                "missing": "0003",
                "size": None,
                "mtime": None,
                "string": os.path.join(self.root, "plate.0001,0002,0004.exr"),
            },
        )
        self.assertEqual(records["comp"]["missing"], "")
        self.assertEqual(
            records["notes.txt"],
            {
                "type": "file",
                "path": self.root,
                "name": "notes.txt",
                "size": None,
                "mtime": None,
                "string": os.path.join(self.root, "notes.txt"),
            },
        )

    def test_long_format_adds_sizes_and_times(self):
        """-l fills in size (bytes) and mtime (epoch seconds)."""
        records = self.records("--json", "-l")
        self.assertEqual(records["plate"]["size"], 15)
        self.assertEqual(records["comp"]["size"], 14)
        self.assertEqual(records["notes.txt"]["size"], 3)
        for record in records.values():
            self.assertIsInstance(record["mtime"], float)

    def test_seqs_only(self):
        """-S leaves the singletons out."""
        self.assertEqual(set(self.records("--json", "-S")), {"plate", "comp"})

    def test_missing_keeps_only_sequences_with_gaps(self):
        """-m lists the gapped sequences, still with their real frames."""
        records = self.records("--json", "-m")
        self.assertEqual(set(records), {"plate"})
        self.assertEqual(records["plate"]["frames"], "0001,0002,0004")
        self.assertEqual(records["plate"]["missing"], "0003")

    def test_no_results_is_an_empty_array(self):
        """Nothing to report is still valid JSON."""
        with tempfile.TemporaryDirectory() as empty_dir:
            for options in (["--json"], ["--json", "-m"]):
                args = seqls.parse_args([*options, empty_dir])
                self.assertEqual(json.loads(seqls.main(args, _debug=True)), [])
        # A directory with only gap-free sequences has nothing for -m.
        for name in os.listdir(self.root):
            if name.startswith("plate") or name == "notes.txt":
                os.remove(os.path.join(self.root, name))
        self.assertEqual(json.loads(self.run_seqls("--json", "-m")), [])

    def test_printed_output_is_only_json(self):
        """No blank line or other text around the JSON on stdout."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            seqls.main(seqls.parse_args(["--json", self.root]))
        text = out.getvalue()
        self.assertTrue(text.startswith("["), text)
        self.assertEqual(len(json.loads(text)), 3)

    def test_windows_paths_survive_json(self):
        """Backslashes and drive letters round-trip."""
        with test_windows_paths.windows_paths():
            fseq = sequences.FileSequence(
                name="C:\\renders\\plate", ext="exr", frames=[1, 2], pad=4
            )
            record = json.loads(seqls.json_output([fseq]))[0]
        self.assertEqual(record["path"], "C:\\renders")
        self.assertEqual(record["string"], "C:\\renders\\plate.0001,0002.exr")
