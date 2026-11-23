"""Tests for the seqcp and seqmv commands (seqparse.cli.seqtransfer)."""

import contextlib
import errno
import io
import os
import tempfile
import unittest
from unittest import mock

from seqparse.cli import seqtransfer


def _touch(directory, name, numbers, size=3):
    """Create plate.NNNN.exr files (the content says which frame)."""
    for number in numbers:
        path = os.path.join(directory, f"{name}.{number:04d}.exr")
        with open(path, "w") as handle:
            handle.write(f"{number}" * size)


class _CommandTestCase(unittest.TestCase):
    """Base class: a source and a destination directory, and a runner."""

    def setUp(self):
        """Create the directories."""
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.src = os.path.join(tmp.name, "src")
        self.dst = os.path.join(tmp.name, "dst")
        os.mkdir(self.src)
        os.mkdir(self.dst)

    def sequence(self, frames="0001-0003", name="plate"):
        """The command line spelling of a sequence in the source directory."""
        return os.path.join(self.src, f"{name}.{frames}.exr")

    def run_command(self, *argv, copy=False):
        """Run seqcp/seqmv; return (status, stdout lines, stderr lines)."""
        out, err = io.StringIO(), io.StringIO()
        args = seqtransfer.parse_args(list(argv), copy=copy)
        status = seqtransfer.main(args, copy=copy, out=out, err=err)
        return status, out.getvalue().splitlines(), err.getvalue().splitlines()

    def names(self, directory):
        """The sorted names in a directory."""
        return sorted(os.listdir(directory))


class TestSeqmv(_CommandTestCase):
    """seqmv."""

    def setUp(self):
        """Three frames in the source directory."""
        super().setUp()
        _touch(self.src, "plate", [1, 2, 3])

    def test_moves_to_a_directory(self):
        """The files arrive and a summary says so."""
        status, out, err = self.run_command(self.sequence(), self.dst)
        self.assertEqual((status, err), (0, []))
        self.assertEqual(
            out,
            [
                "moved 3 files: "
                + self.sequence()
                + " -> "
                + os.path.join(self.dst, "plate.0001-0003.exr")
            ],
        )
        self.assertEqual(self.names(self.src), [])
        self.assertEqual(len(self.names(self.dst)), 3)

    def test_renumbers_in_place(self):
        """No destination: the files stay where they are, renumbered."""
        status, out, _ = self.run_command("--offset", "1000", self.sequence())
        self.assertEqual(status, 0)
        self.assertTrue(out[0].startswith("moved 3 files:"))
        self.assertEqual(
            self.names(self.src),
            ["plate.1001.exr", "plate.1002.exr", "plate.1003.exr"],
        )

    def test_start_a_negative_offset_and_names(self):
        """--start, --offset=-N, --name and --pad."""
        self.run_command("--start", "10", self.sequence())
        self.assertEqual(
            self.names(self.src),
            ["plate.0010.exr", "plate.0011.exr", "plate.0012.exr"],
        )
        self.run_command(
            "--offset=-9", "--name", "comp", self.sequence("0010-0012")
        )
        self.assertEqual(
            self.names(self.src),
            ["comp.0001.exr", "comp.0002.exr", "comp.0003.exr"],
        )
        self.run_command("--pad", "6", self.sequence("0001-0003", "comp"))
        self.assertEqual(
            self.names(self.src),
            ["comp.000001.exr", "comp.000002.exr", "comp.000003.exr"],
        )

    def test_a_range_of_frames_moves_only_those(self):
        """The rest of the sequence stays."""
        status, out, _ = self.run_command(self.sequence("0002-0003"), self.dst)
        self.assertEqual(status, 0)
        self.assertTrue(out[0].startswith("moved 2 files:"))
        self.assertEqual(self.names(self.src), ["plate.0001.exr"])

    def test_dry_run_changes_nothing(self):
        """-n lists the pairs and the summary."""
        before = self.names(self.src), self.names(self.dst)
        status, out, _ = self.run_command("-n", self.sequence(), self.dst)
        self.assertEqual(status, 0)
        self.assertEqual(len(out), 4)
        self.assertEqual(out[0].split(" -> ")[0], self.sequence("0001"))
        self.assertTrue(out[-1].startswith("would move 3 files:"))
        self.assertEqual((self.names(self.src), self.names(self.dst)), before)

    def test_verbose_lists_every_file(self):
        """-v prints the pairs, then the summary."""
        status, out, _ = self.run_command("-v", self.sequence(), self.dst)
        self.assertEqual(status, 0)
        self.assertEqual(len(out), 4)
        self.assertTrue(out[-1].startswith("moved 3 files:"))

    def test_nothing_to_do(self):
        """Moving a sequence onto itself."""
        status, out, err = self.run_command(self.sequence())
        self.assertEqual((status, out, err), (0, ["nothing to do"], []))

    def test_problems_are_reported_and_nothing_changes(self):
        """Exit status 1, messages on stderr, files untouched."""
        _touch(self.dst, "plate", [2])
        status, out, err = self.run_command(self.sequence(), self.dst)
        self.assertEqual((status, out), (1, []))
        self.assertEqual(len(err), 1)
        self.assertIn("seqmv: destination exists:", err[0])
        self.assertEqual(len(self.names(self.src)), 3)

    def test_force_replaces_existing_files(self):
        """-f."""
        _touch(self.dst, "plate", [2], size=1)
        status, _, err = self.run_command("-f", self.sequence(), self.dst)
        self.assertEqual((status, err), (0, []))
        with open(os.path.join(self.dst, "plate.0002.exr")) as handle:
            self.assertEqual(handle.read(), "222")

    def test_parents_creates_the_directory(self):
        """-p; without it the directory is a problem."""
        target = os.path.join(self.dst, "new", "deeper")
        status, _, err = self.run_command(self.sequence(), target)
        self.assertEqual(status, 1)
        self.assertIn("destination directory does not exist", err[0])
        status, _, _ = self.run_command("-p", self.sequence(), target)
        self.assertEqual(status, 0)
        self.assertEqual(len(self.names(target)), 3)

    def test_missing_files_are_a_problem(self):
        """A frame that is not on disk."""
        status, _, err = self.run_command(self.sequence("0001-0005"), self.dst)
        self.assertEqual(status, 1)
        self.assertEqual(len(err), 2)
        self.assertTrue(all("source does not exist" in e for e in err))

    def test_many_problems_are_summarized(self):
        """A common problem on a long sequence does not flood the terminal."""
        _touch(self.src, "long", range(1, 31))
        _touch(self.dst, "long", range(1, 31))
        status, _, err = self.run_command(
            self.sequence("0001-0030", "long"), self.dst
        )
        self.assertEqual(status, 1)
        self.assertEqual(len(err), 11)
        self.assertEqual(err[-1], "seqmv: ... and 20 more problems")

    def test_not_a_file_sequence(self):
        """A plain file name."""
        status, out, err = self.run_command(
            os.path.join(self.src, "notes.txt"), self.dst
        )
        self.assertEqual((status, out), (1, []))
        self.assertIn("not a file sequence", err[0])

    def test_impossible_numbers(self):
        """Frames below 0 are an error message, not a traceback."""
        status, _, err = self.run_command("--offset=-9", self.sequence())
        self.assertEqual(status, 1)
        self.assertIn("below 0", err[0])

    def test_start_and_offset_conflict(self):
        """argparse refuses (exit status 2)."""
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as caught,
        ):
            seqtransfer.parse_args(
                ["--start", "1", "--offset", "2", "x.0001.exr"], copy=False
            )
        self.assertEqual(caught.exception.code, 2)

    def test_a_failure_is_undone_and_reported(self):
        """Exit status 1, and the message says what happened."""
        real = os.rename
        calls = []

        def rename(src, dst):
            calls.append(src)
            if len(calls) == 2:
                raise PermissionError(errno.EACCES, "in use", src)
            return real(src, dst)

        with mock.patch("os.rename", rename):
            status, out, err = self.run_command(self.sequence(), self.dst)
        self.assertEqual((status, out), (1, []))
        self.assertIn("seqmv: everything done so far was undone", err)
        self.assertEqual(len(self.names(self.src)), 3)
        self.assertEqual(self.names(self.dst), [])

    def test_an_undo_that_fails_is_reported(self):
        """The messages say what could not be put back."""
        real = os.rename
        calls = []

        def rename(src, dst):
            calls.append(src)
            if len(calls) >= 2:
                raise PermissionError(errno.EACCES, "in use", src)
            return real(src, dst)

        with mock.patch("os.rename", rename):
            status, _, err = self.run_command(self.sequence(), self.dst)
        self.assertEqual(status, 1)
        self.assertFalse(any("undone" in line for line in err))
        self.assertTrue(any("could not undo" in line for line in err))


class TestSeqcp(_CommandTestCase):
    """seqcp."""

    def setUp(self):
        """Three frames in the source directory."""
        super().setUp()
        _touch(self.src, "plate", [1, 2, 3])

    def test_copies_to_a_directory(self):
        """The originals stay."""
        status, out, err = self.run_command(
            self.sequence(), self.dst, copy=True
        )
        self.assertEqual((status, err), (0, []))
        self.assertTrue(out[0].startswith("copied 3 files:"))
        self.assertEqual(len(self.names(self.src)), 3)
        self.assertEqual(len(self.names(self.dst)), 3)

    def test_copies_with_a_new_number_and_name(self):
        """--offset and --name together."""
        status, _, _ = self.run_command(
            "--offset",
            "100",
            "--name",
            "comp",
            self.sequence(),
            self.dst,
            copy=True,
        )
        self.assertEqual(status, 0)
        self.assertEqual(
            self.names(self.dst),
            ["comp.0101.exr", "comp.0102.exr", "comp.0103.exr"],
        )

    def test_a_copy_onto_itself_is_a_problem(self):
        """Unlike a move, which has nothing to do."""
        status, _, err = self.run_command(self.sequence(), copy=True)
        self.assertEqual(status, 1)
        self.assertIn("source and destination are the same", err[0])

    def test_dry_run_says_would_copy(self):
        """-n."""
        status, out, _ = self.run_command(
            "-n", self.sequence(), self.dst, copy=True
        )
        self.assertEqual(status, 0)
        self.assertTrue(out[-1].startswith("would copy 3 files:"))
        self.assertEqual(self.names(self.dst), [])
