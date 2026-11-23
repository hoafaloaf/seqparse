"""Tests for copying, moving and renumbering sequences (seqparse.transfer)."""

import copy
import errno
import os
import pickle
import random
import shutil
import tempfile
import unittest
from unittest import mock

from seqparse import sequences, transfer


def _name(directory, name, number, pad=4, ext="exr"):
    """The path of one frame."""
    return os.path.join(directory, f"{name}.{number:0{pad}d}.{ext}")


def _make(directory, name, frames, pad=4, ext="exr"):
    """Create files whose content says which frame they are."""
    for number in frames:
        with open(_name(directory, name, number, pad, ext), "w") as handle:
            handle.write(f"{name} {number}")


def _seq(directory, name, frames, pad=4, ext="exr"):
    """The FileSequence for those files."""
    return sequences.FileSequence(
        name=os.path.join(directory, name),
        ext=ext,
        frames=list(frames),
        pad=pad,
    )


def _content(directory, name, number, pad=4, ext="exr"):
    """What a frame's file says (or None when it does not exist)."""
    try:
        with open(_name(directory, name, number, pad, ext)) as handle:
            return handle.read()
    except FileNotFoundError:
        return None


def _listing(directory):
    """The sorted names in a directory."""
    return sorted(os.listdir(directory))


class _TempDirs(unittest.TestCase):
    """Base class: a source directory and a destination directory."""

    def setUp(self):
        """Create the directories."""
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.src = os.path.join(self.root, "src")
        self.dst = os.path.join(self.root, "dst")
        os.mkdir(self.src)
        os.mkdir(self.dst)


class TestPlanning(_TempDirs):
    """What plan_move and plan_copy work out."""

    def test_planning_touches_nothing(self):
        """A plan only looks."""
        _make(self.src, "plate", [1, 2, 3])
        before = _listing(self.src), _listing(self.dst)
        plan = transfer.plan_move(_seq(self.src, "plate", [1, 2, 3]), self.dst)
        self.assertEqual(plan.problems, [])
        self.assertEqual(len(plan.pairs), 3)
        self.assertEqual((_listing(self.src), _listing(self.dst)), before)

    def test_move_to_another_directory(self):
        """The files arrive, the originals are gone."""
        _make(self.src, "plate", [1, 2, 3])
        plan = transfer.plan_move(_seq(self.src, "plate", [1, 2, 3]), self.dst)
        result = plan.execute()
        self.assertEqual(_listing(self.src), [])
        self.assertEqual(
            _listing(self.dst),
            ["plate.0001.exr", "plate.0002.exr", "plate.0003.exr"],
        )
        self.assertEqual(
            str(result), os.path.join(self.dst, "plate.0001-0003.exr")
        )

    def test_copy_keeps_the_originals_and_modification_times(self):
        """Copies are independent files with the same timestamps."""
        _make(self.src, "plate", [1, 2])
        for number, mtime in ((1, 1_000_000_000), (2, 1_100_000_000)):
            os.utime(_name(self.src, "plate", number), (mtime, mtime))
        transfer.plan_copy(_seq(self.src, "plate", [1, 2]), self.dst).execute()
        self.assertEqual(len(_listing(self.src)), 2)
        for number, mtime in ((1, 1_000_000_000), (2, 1_100_000_000)):
            copy = _name(self.dst, "plate", number)
            self.assertEqual(int(os.stat(copy).st_mtime), mtime)
            self.assertEqual(
                _content(self.dst, "plate", number), f"plate {number}"
            )

    def test_offset_renumbers(self):
        """Every frame number moves by the offset."""
        _make(self.src, "plate", [1, 2, 3])
        plan = transfer.plan_move(
            _seq(self.src, "plate", [1, 2, 3]), offset=1000
        )
        plan.execute()
        self.assertEqual(
            _listing(self.src),
            ["plate.1001.exr", "plate.1002.exr", "plate.1003.exr"],
        )

    def test_start_renumbers_and_keeps_gaps(self):
        """The first frame becomes `start`; the gaps stay gaps."""
        _make(self.src, "plate", [3, 4, 10])
        plan = transfer.plan_copy(
            _seq(self.src, "plate", [3, 4, 10]), self.dst, start=100
        )
        plan.execute()
        self.assertEqual(
            _listing(self.dst),
            ["plate.0100.exr", "plate.0101.exr", "plate.0107.exr"],
        )

    def test_new_name_and_padding(self):
        """name= renames the sequence, pad= re-pads the frame numbers."""
        _make(self.src, "plate", [1, 2])
        plan = transfer.plan_move(
            _seq(self.src, "plate", [1, 2]), name="comp", pad=6
        )
        plan.execute()
        self.assertEqual(
            _listing(self.src), ["comp.000001.exr", "comp.000002.exr"]
        )
        self.assertEqual(plan.result.pad, 6)

    def test_numbers_longer_than_the_padding_use_more_digits(self):
        """Padding 3 and frame 1001: no truncation."""
        _make(self.src, "plate", [1, 2], pad=3)
        transfer.plan_move(
            _seq(self.src, "plate", [1, 2], pad=3), offset=999
        ).execute()
        self.assertEqual(
            _listing(self.src), ["plate.1000.exr", "plate.1001.exr"]
        )

    def test_only_the_frames_of_the_sequence_are_transferred(self):
        """Other files in the directory, and other frames, stay put."""
        _make(self.src, "plate", [1, 2, 3, 4])
        _make(self.src, "other", [1])
        transfer.plan_move(_seq(self.src, "plate", [2, 3]), self.dst).execute()
        self.assertEqual(
            _listing(self.src),
            ["other.0001.exr", "plate.0001.exr", "plate.0004.exr"],
        )

    def test_frames_only_names_work(self):
        """Sequences without a base name (0001.exr)."""
        for number in (1, 2):
            with open(os.path.join(self.src, f"{number:04d}.exr"), "w"):
                pass
        fseq = sequences.FileSequence(
            name=None, ext="exr", frames=[1, 2], pad=4
        )
        fseq.path = self.src
        transfer.plan_move(fseq, offset=10).execute()
        self.assertEqual(_listing(self.src), ["0011.exr", "0012.exr"])

    def test_bad_arguments(self):
        """Contradictory or impossible requests are errors, not problems."""
        _make(self.src, "plate", [1, 2])
        fseq = _seq(self.src, "plate", [1, 2])
        with self.assertRaises(ValueError):
            transfer.plan_move(fseq, offset=1, start=5)
        with self.assertRaises(ValueError):
            transfer.plan_move(fseq, offset=-2)  # frame -1
        with self.assertRaises(ValueError):
            transfer.plan_move(fseq, start=-1)
        with self.assertRaises(ValueError):
            transfer.plan_move(fseq, pad=0)
        with self.assertRaises(ValueError):
            transfer.plan_move(
                sequences.FileSequence(frames=[1], pad=4), offset=1
            )

    def test_repr(self):
        """The plan describes itself."""
        _make(self.src, "plate", [1])
        plan = transfer.plan_move(_seq(self.src, "plate", [1]), self.dst)
        self.assertEqual(repr(plan), "Plan(move, 1 files, 0 problems)")


class TestProblems(_TempDirs):
    """Everything that stands in the way is reported before any change."""

    def test_missing_sources(self):
        """A listed frame that is not on disk."""
        _make(self.src, "plate", [1, 3])
        plan = transfer.plan_move(_seq(self.src, "plate", [1, 2, 3]), self.dst)
        self.assertEqual(
            plan.problems,
            [f"source does not exist: {_name(self.src, 'plate', 2)}"],
        )

    def test_a_plan_with_problems_refuses_to_run(self):
        """Nothing is touched."""
        _make(self.src, "plate", [1, 3])
        plan = transfer.plan_move(_seq(self.src, "plate", [1, 2, 3]), self.dst)
        with self.assertRaises(ValueError):
            plan.execute()
        self.assertEqual(len(_listing(self.src)), 2)
        self.assertEqual(_listing(self.dst), [])

    def test_a_directory_is_not_a_file(self):
        """Only files are transferred."""
        os.mkdir(_name(self.src, "plate", 1))
        plan = transfer.plan_move(_seq(self.src, "plate", [1]), self.dst)
        self.assertEqual(
            plan.problems, [f"not a file: {_name(self.src, 'plate', 1)}"]
        )

    def test_an_unreadable_source_is_a_problem(self):
        """Not only "does not exist": permissions and the like."""
        _make(self.src, "plate", [1])
        target = _name(self.src, "plate", 1)
        real = os.lstat

        def lstat(path, *args, **kwargs):
            if path == target:
                raise PermissionError(errno.EACCES, "Permission denied", path)
            return real(path, *args, **kwargs)

        with mock.patch("os.lstat", lstat):
            plan = transfer.plan_move(_seq(self.src, "plate", [1]), self.dst)
        self.assertEqual(
            plan.problems, [f"cannot read {target}: Permission denied"]
        )

    def test_two_files_to_one_destination(self):
        """Cannot happen through the public API, but it is guarded."""
        problems = []
        target = os.path.join(self.dst, "x")
        transfer._check_destinations(
            "copy",
            [("a", target), ("b", target)],
            [None, None],
            False,
            problems,
        )
        self.assertEqual(problems, [f"two files would be written to {target}"])

    def test_existing_destinations_are_never_overwritten(self):
        """Without overwrite=True."""
        _make(self.src, "plate", [1, 2])
        _make(self.dst, "plate", [2])
        plan = transfer.plan_copy(_seq(self.src, "plate", [1, 2]), self.dst)
        self.assertEqual(
            plan.problems,
            [f"destination exists: {_name(self.dst, 'plate', 2)}"],
        )
        self.assertEqual(_content(self.dst, "plate", 2), "plate 2")

    def test_overwrite_replaces_unrelated_files(self):
        """overwrite=True is the way to replace them."""
        _make(self.src, "plate", [2])
        with open(_name(self.dst, "plate", 2), "w") as handle:
            handle.write("old")
        plan = transfer.plan_move(
            _seq(self.src, "plate", [2]), self.dst, overwrite=True
        )
        self.assertEqual(plan.problems, [])
        plan.execute()
        self.assertEqual(_content(self.dst, "plate", 2), "plate 2")

    def test_a_missing_destination_directory(self):
        """It must exist, unless parents=True."""
        _make(self.src, "plate", [1])
        target = os.path.join(self.root, "new", "deeper")
        fseq = _seq(self.src, "plate", [1])
        plan = transfer.plan_copy(fseq, target)
        self.assertEqual(
            plan.problems, [f"destination directory does not exist: {target}"]
        )
        plan = transfer.plan_copy(fseq, target, parents=True)
        self.assertEqual(plan.problems, [])
        plan.execute()
        self.assertEqual(_content(target, "plate", 1), "plate 1")

    def test_moving_onto_itself_is_a_no_op(self):
        """Nothing to do, nothing wrong."""
        _make(self.src, "plate", [1, 2])
        plan = transfer.plan_move(_seq(self.src, "plate", [1, 2]))
        self.assertEqual((plan.pairs, plan.problems), ([], []))
        self.assertEqual(plan.execute().pad, 4)

    def test_copying_onto_itself_is_a_problem(self):
        """A copy needs somewhere else to go."""
        _make(self.src, "plate", [1])
        plan = transfer.plan_copy(_seq(self.src, "plate", [1]))
        self.assertEqual(
            plan.problems,
            [
                "source and destination are the same: "
                + _name(self.src, "plate", 1)
            ],
        )

    def test_an_unrelated_file_blocks_an_in_place_shift(self):
        """A file that is not part of the sequence is not overwritten."""
        _make(self.src, "plate", [1, 2, 3])
        _make(self.src, "plate", [5], pad=4)
        plan = transfer.plan_move(_seq(self.src, "plate", [1, 2, 3]), offset=4)
        self.assertEqual(
            plan.problems,
            [f"destination exists: {_name(self.src, 'plate', 5)}"],
        )

    def test_an_overlapping_copy_needs_overwrite(self):
        """Copying 1-3 to 2-4 would destroy sources."""
        _make(self.src, "plate", [1, 2, 3])
        fseq = _seq(self.src, "plate", [1, 2, 3])
        plan = transfer.plan_copy(fseq, offset=1)
        self.assertEqual(len(plan.problems), 2)
        self.assertTrue(all("also a source" in p for p in plan.problems))
        plan = transfer.plan_copy(fseq, offset=1, overwrite=True)
        self.assertEqual(plan.problems, [])
        plan.execute()
        # Each file was read before it was overwritten.
        self.assertEqual(
            [_content(self.src, "plate", n) for n in (1, 2, 3, 4)],
            ["plate 1", "plate 1", "plate 2", "plate 3"],
        )

    def test_a_file_waits_for_everything_it_depends_on(self):
        """Pair 2 may only run after both pair 0 and pair 1."""
        problems = []
        pairs = [("a", "1"), ("b", "2"), ("c", "3")]
        ordered = transfer._order(pairs, {2: {0, 1}}, problems)
        self.assertEqual((ordered, problems), (pairs, []))

    def test_unorderable_moves_are_refused(self):
        """A swap cannot be done without overwriting a source."""
        problems = []
        ordered = transfer._order(
            [("a", "b"), ("b", "a"), ("c", "d")], {0: {1}, 1: {0}}, problems
        )
        self.assertEqual(ordered, [("c", "d")])
        self.assertEqual(len(problems), 1)
        self.assertIn("a, b", problems[0])

    def test_a_case_only_rename_is_never_silently_dropped(self):
        """Windows folds case in paths; that must not turn it into a no-op."""
        _make(self.src, "Plate", [1])
        with mock.patch("os.path.normcase", str.lower):
            plan = transfer.plan_move(
                _seq(self.src, "Plate", [1]), name="plate"
            )
        self.assertEqual(len(plan.pairs), 1)

    def test_case_only_collisions(self):
        """On a case-insensitive filesystem Plate and plate are one file."""
        _make(self.src, "Plate", [1])
        if not os.path.exists(_name(self.src, "plate", 1)):
            self.skipTest("this filesystem is case-sensitive")
        plan = transfer.plan_move(_seq(self.src, "Plate", [1]), name="plate")
        self.assertEqual(len(plan.problems), 1)
        self.assertIn("same file as its source", plan.problems[0])

    def test_symlinks(self):
        """A moved link stays a link; a copied link becomes a real file."""
        _make(self.root, "target", [1])
        link = _name(self.src, "plate", 1)
        try:
            os.symlink(_name(self.root, "target", 1), link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not available")
        fseq = _seq(self.src, "plate", [1])
        transfer.plan_copy(fseq, self.dst).execute()
        copied = _name(self.dst, "plate", 1)
        self.assertFalse(os.path.islink(copied))
        self.assertEqual(_content(self.dst, "plate", 1), "target 1")
        transfer.plan_move(fseq, offset=5).execute()
        self.assertTrue(os.path.islink(_name(self.src, "plate", 6)))
        self.assertFalse(os.path.lexists(link))


class TestOverlappingRanges(_TempDirs):
    """Shifting a sequence within its own directory."""

    def test_shift_up(self):
        """+1 on 1-5: the highest frame goes first."""
        _make(self.src, "plate", range(1, 6))
        plan = transfer.plan_move(
            _seq(self.src, "plate", range(1, 6)), offset=1
        )
        self.assertEqual(plan.problems, [])
        self.assertEqual(
            [dst for _, dst in plan.pairs],
            [_name(self.src, "plate", n) for n in (6, 5, 4, 3, 2)],
        )
        plan.execute()
        self.assertEqual(
            [_content(self.src, "plate", n) for n in range(1, 7)],
            [None] + [f"plate {n}" for n in range(1, 6)],
        )

    def test_shift_down(self):
        """-1 on 2-6: the lowest frame goes first."""
        _make(self.src, "plate", range(2, 7))
        plan = transfer.plan_move(
            _seq(self.src, "plate", range(2, 7)), offset=-1
        )
        self.assertEqual(
            [src for src, _ in plan.pairs],
            [_name(self.src, "plate", n) for n in range(2, 7)],
        )
        plan.execute()
        self.assertEqual(
            [_content(self.src, "plate", n) for n in range(1, 7)],
            [f"plate {n + 1}" for n in range(1, 6)] + [None],
        )

    def test_randomized_shifts_never_lose_a_file(self):
        """Any frames, any offset: every file ends up where it belongs."""
        rng = random.Random(20261122)
        for _ in range(150):
            frames = sorted(rng.sample(range(30), rng.randint(1, 12)))
            offset = rng.randint(-min(frames), 40)
            with tempfile.TemporaryDirectory() as directory:
                _make(directory, "p", frames)
                plan = transfer.plan_move(
                    _seq(directory, "p", frames), offset=offset
                )
                context = (frames, offset)
                self.assertEqual(plan.problems, [], context)
                plan.execute()
                expected = {
                    os.path.basename(
                        _name(directory, "p", n + offset)
                    ): f"p {n}"
                    for n in frames
                }
                actual = {}
                for name in os.listdir(directory):
                    with open(os.path.join(directory, name)) as handle:
                        actual[name] = handle.read()
                self.assertEqual(actual, expected, context)

    def test_randomized_copies_leave_the_originals_alone(self):
        """Copying elsewhere with an offset changes nothing at the source."""
        rng = random.Random(7)
        for _ in range(40):
            frames = sorted(rng.sample(range(30), rng.randint(1, 10)))
            offset = rng.randint(-min(frames), 40)
            with tempfile.TemporaryDirectory() as directory:
                src, dst = (
                    os.path.join(directory, "s"),
                    os.path.join(directory, "d"),
                )
                os.mkdir(src)
                os.mkdir(dst)
                _make(src, "p", frames)
                transfer.plan_copy(
                    _seq(src, "p", frames), dst, offset=offset
                ).execute()
                for number in frames:
                    self.assertEqual(_content(src, "p", number), f"p {number}")
                    self.assertEqual(
                        _content(dst, "p", number + offset), f"p {number}"
                    )


class TestFailures(_TempDirs):
    """A transfer that fails part way."""

    def setUp(self):
        """Five files to move."""
        super().setUp()
        _make(self.src, "plate", range(1, 6))
        self.fseq = _seq(self.src, "plate", range(1, 6))

    def _flaky(self, real, fail_from):
        """A stand-in for a rename function that fails from call N on."""
        calls = []

        def rename(src, dst):
            calls.append((src, dst))
            if len(calls) >= fail_from:
                raise PermissionError(errno.EACCES, "in use", src)
            return real(src, dst)

        return rename

    def test_a_failed_move_is_undone(self):
        """The completed renames are renamed back."""
        plan = transfer.plan_move(self.fseq, self.dst)
        real = transfer._rename_exclusive
        calls = []

        def rename(src, dst):
            calls.append(src)
            if len(calls) == 3:
                raise PermissionError(errno.EACCES, "in use", src)
            return real(src, dst)

        with (
            mock.patch.object(transfer, "_rename_exclusive", rename),
            self.assertRaises(transfer.TransferError) as caught,
        ):
            plan.execute()
        error = caught.exception
        self.assertEqual(len(error.done), 2)
        self.assertEqual(error.failed, plan.pairs[2])
        self.assertTrue(error.rolled_back)
        self.assertEqual(error.rollback_errors, [])
        self.assertEqual(len(_listing(self.src)), 5)
        self.assertEqual(_listing(self.dst), [])
        self.assertIsInstance(error.__cause__, PermissionError)

    def test_an_undo_that_fails_is_reported(self):
        """The error says what could not be put back."""
        plan = transfer.plan_move(self.fseq, self.dst)
        with (
            mock.patch.object(
                transfer,
                "_rename_exclusive",
                self._flaky(transfer._rename_exclusive, 3),
            ),
            self.assertRaises(transfer.TransferError) as caught,
        ):
            plan.execute()
        error = caught.exception
        self.assertFalse(error.rolled_back)
        self.assertEqual(len(error.rollback_errors), 2)
        self.assertEqual(len(_listing(self.dst)), 2)  # still there, not lost

    def test_a_failed_copy_removes_the_copies_it_made(self):
        """Only the new files; the originals are untouched."""
        real = shutil.copy2
        calls = []

        def copy2(src, dst, **kwargs):
            calls.append(src)
            if len(calls) == 4:
                with open(dst, "w") as partial:
                    partial.write("half a fra")
                raise OSError(errno.ENOSPC, "no space left", src)
            return real(src, dst, **kwargs)

        plan = transfer.plan_copy(self.fseq, self.dst)
        with (
            mock.patch("shutil.copy2", copy2),
            self.assertRaises(transfer.TransferError) as caught,
        ):
            plan.execute()
        self.assertTrue(caught.exception.rolled_back)
        self.assertEqual(_listing(self.dst), [])  # also no partial file
        self.assertEqual(len(_listing(self.src)), 5)

    def test_a_failed_overwriting_copy_keeps_the_existing_file(self):
        """No cleanup of a destination that was there before."""
        with open(_name(self.dst, "plate", 1), "w") as handle:
            handle.write("old")
        plan = transfer.plan_copy(self.fseq, self.dst, overwrite=True)
        with (
            mock.patch(
                "shutil.copy2", side_effect=OSError(errno.EIO, "disk error")
            ),
            self.assertRaises(transfer.TransferError),
        ):
            plan.execute()
        self.assertEqual(_content(self.dst, "plate", 1), "old")

    def test_overwritten_files_cannot_be_restored(self):
        """The error admits it."""
        with open(_name(self.dst, "plate", 1), "w") as handle:
            handle.write("old")
        plan = transfer.plan_move(self.fseq, self.dst, overwrite=True)
        with (
            mock.patch("os.replace", self._flaky(os.replace, 3)),
            self.assertRaises(transfer.TransferError) as caught,
        ):
            plan.execute()
        error = caught.exception
        self.assertFalse(error.rolled_back)
        self.assertTrue(any("overwritten" in e for e in error.rollback_errors))

    def test_moving_across_filesystems_copies_then_deletes(self):
        """EXDEV from rename: copy2, then delete the original."""
        os.utime(_name(self.src, "plate", 1), (1_000_000_000, 1_000_000_000))
        plan = transfer.plan_move(self.fseq, self.dst)
        cross_device = OSError(errno.EXDEV, "cross-device link")
        with mock.patch.object(
            transfer, "_rename_exclusive", side_effect=cross_device
        ):
            plan.execute()
        self.assertEqual(_listing(self.src), [])
        self.assertEqual(len(_listing(self.dst)), 5)
        copy = _name(self.dst, "plate", 1)
        self.assertEqual(int(os.stat(copy).st_mtime), 1_000_000_000)

    def test_the_original_survives_a_failed_cross_filesystem_copy(self):
        """No deletion unless the copy worked, and no partial file."""

        def copy2(src, dst, **kwargs):
            with open(dst, "w") as partial:
                partial.write("half a fra")
            raise OSError(errno.EIO, "disk error", src)

        plan = transfer.plan_move(self.fseq, self.dst)
        with (
            mock.patch.object(
                transfer,
                "_rename_exclusive",
                side_effect=OSError(errno.EXDEV, "cross-device"),
            ),
            mock.patch("shutil.copy2", copy2),
            self.assertRaises(transfer.TransferError),
        ):
            plan.execute()
        self.assertEqual(len(_listing(self.src)), 5)
        self.assertEqual(_listing(self.dst), [])


class TestHazards(_TempDirs):
    """Awkward things found at the destination, or in the arguments."""

    def setUp(self):
        """Three frames to transfer."""
        super().setUp()
        _make(self.src, "plate", [1, 2, 3])
        self.fseq = _seq(self.src, "plate", [1, 2, 3])

    def _can_link(self):
        """Skip unless symlinks and hard links work here."""
        try:
            os.symlink(
                os.path.join(self.root, "x"), os.path.join(self.root, "y")
            )
            os.link(_name(self.src, "plate", 1), os.path.join(self.root, "z"))
        except (OSError, NotImplementedError):
            self.skipTest("links are not available")

    def test_a_file_that_appears_after_planning_is_not_overwritten(self):
        """The check at plan time is not the only protection."""
        for plan_for in (transfer.plan_move, transfer.plan_copy):
            with self.subTest(plan_for=plan_for.__name__):
                plan = plan_for(self.fseq, self.dst)
                self.assertEqual(plan.problems, [])
                late = _name(self.dst, "plate", 2)
                with open(late, "w") as handle:
                    handle.write("written by someone else")
                with self.assertRaises(transfer.TransferError):
                    plan.execute()
                with open(late) as handle:
                    self.assertEqual(handle.read(), "written by someone else")
                self.assertEqual(len(_listing(self.src)), 3)
                os.unlink(late)
                for name in _listing(self.dst):
                    os.unlink(os.path.join(self.dst, name))

    def test_a_symlink_destination_is_replaced_not_followed(self):
        """-f replaces the link; it never writes through it."""
        self._can_link()
        target = os.path.join(self.root, "target.txt")
        with open(target, "w") as handle:
            handle.write("precious")
        os.symlink(target, _name(self.dst, "plate", 2))
        transfer.plan_copy(self.fseq, self.dst, overwrite=True).execute()
        with open(target) as handle:
            self.assertEqual(handle.read(), "precious")
        self.assertFalse(os.path.islink(_name(self.dst, "plate", 2)))
        self.assertEqual(_content(self.dst, "plate", 2), "plate 2")

    def test_a_hard_linked_destination_is_not_written_through(self):
        """Replacing a hard link must not change the other names."""
        self._can_link()
        other = os.path.join(self.root, "other.txt")
        with open(other, "w") as handle:
            handle.write("shared")
        os.link(other, _name(self.dst, "plate", 2))
        transfer.plan_copy(self.fseq, self.dst, overwrite=True).execute()
        with open(other) as handle:
            self.assertEqual(handle.read(), "shared")

    def test_a_directory_destination_is_a_problem(self):
        """Even with overwrite: a file cannot replace a directory."""
        os.mkdir(_name(self.dst, "plate", 3))
        for overwrite in (False, True):
            plan = transfer.plan_copy(self.fseq, self.dst, overwrite=overwrite)
            self.assertIn(
                f"destination is a directory: {_name(self.dst, 'plate', 3)}",
                plan.problems,
            )

    def test_a_hard_link_of_a_source_is_an_unrelated_file(self):
        """It is not "one of ours" just because it is the same inode."""
        self._can_link()
        os.link(_name(self.src, "plate", 2), _name(self.dst, "plate", 1001))
        plan = transfer.plan_move(self.fseq, self.dst, offset=1000)
        self.assertEqual(
            plan.problems,
            [f"destination exists: {_name(self.dst, 'plate', 1001)}"],
        )

    def test_a_name_may_not_contain_a_directory(self):
        """Use dest for that; the result's path would be wrong."""
        for bad in ("sub/q", "sub" + os.sep + "q"):
            with self.subTest(name=bad), self.assertRaises(ValueError):
                transfer.plan_move(self.fseq, self.dst, name=bad)

    def test_the_same_directory_spelled_differently_is_the_same(self):
        """./a and a/../a are one directory: a no-op, not a problem."""
        spelled = os.path.join(self.src, "..", "src")
        plan = transfer.plan_move(self.fseq, spelled)
        self.assertEqual((plan.pairs, plan.problems), ([], []))
        plan = transfer.plan_copy(self.fseq, spelled)
        self.assertEqual(len(plan.problems), 3)

    def test_a_transfer_error_survives_pickling_and_copying(self):
        """Worker processes pass exceptions around."""
        error = transfer.TransferError(
            "it broke", [("a", "b")], ("c", "d"), False, ["x"]
        )
        for clone in (pickle.loads(pickle.dumps(error)), copy.copy(error)):
            self.assertEqual(str(clone), "it broke")
            self.assertEqual(
                (
                    clone.done,
                    clone.failed,
                    clone.rolled_back,
                    clone.rollback_errors,
                ),
                ([("a", "b")], ("c", "d"), False, ["x"]),
            )

    def test_a_failed_transfer_removes_the_directories_it_created(self):
        """parents=True is undone too."""
        target = os.path.join(self.dst, "new", "deeper")
        real = shutil.copy2
        calls = []

        def copy2(src, dst, **kwargs):
            calls.append(src)
            if len(calls) == 2:
                raise OSError(errno.ENOSPC, "no space left", src)
            return real(src, dst, **kwargs)

        plan = transfer.plan_copy(self.fseq, target, parents=True)
        with (
            mock.patch("shutil.copy2", copy2),
            self.assertRaises(transfer.TransferError),
        ):
            plan.execute()
        self.assertEqual(_listing(self.dst), [])

    def test_moving_a_symlink_across_filesystems_over_an_existing_file(self):
        """The copy fallback must replace the destination like os.replace."""
        self._can_link()
        target = os.path.join(self.root, "target.txt")
        with open(target, "w") as handle:
            handle.write("t")
        link = _name(self.src, "link", 1)
        os.symlink(target, link)
        with open(_name(self.dst, "link", 1), "w") as handle:
            handle.write("old")
        plan = transfer.plan_move(
            _seq(self.src, "link", [1]), self.dst, overwrite=True
        )
        real = os.replace

        def replace(src, dst):
            if src == link:  # only moving the original crosses a device
                raise OSError(errno.EXDEV, "cross-device link", src)
            return real(src, dst)

        with mock.patch("os.replace", replace):
            plan.execute()
        self.assertTrue(os.path.islink(_name(self.dst, "link", 1)))
        self.assertFalse(os.path.lexists(link))


class TestRenamePrimitives(_TempDirs):
    """_rename_exclusive and the copy that replaces atomically."""

    def setUp(self):
        """One file to move."""
        super().setUp()
        _make(self.src, "plate", [1])
        self.a = _name(self.src, "plate", 1)
        self.b = _name(self.dst, "plate", 1)

    @unittest.skipIf(os.name == "nt", "POSIX rename semantics")
    def test_an_existing_destination_is_never_replaced(self):
        """Where plain rename would silently replace it."""
        with open(self.b, "w") as handle:
            handle.write("theirs")
        with self.assertRaises(FileExistsError):
            transfer._rename_exclusive(self.a, self.b)
        self.assertEqual(_content(self.dst, "plate", 1), "theirs")
        self.assertEqual(_content(self.src, "plate", 1), "plate 1")

    @unittest.skipIf(os.name == "nt", "POSIX rename semantics")
    def test_without_hard_links_it_falls_back_to_rename(self):
        """Some filesystems cannot link; the move still works."""
        for failure in (
            OSError(errno.EPERM, "not permitted"),
            NotImplementedError("no follow_symlinks"),
        ):
            with self.subTest(failure=type(failure).__name__):
                with mock.patch("os.link", side_effect=failure):
                    transfer._rename_exclusive(self.a, self.b)
                self.assertEqual(_content(self.dst, "plate", 1), "plate 1")
                os.rename(self.b, self.a)

    @unittest.skipIf(os.name == "nt", "POSIX rename semantics")
    def test_crossing_a_device_is_left_to_the_caller(self):
        """EXDEV is passed on, so the move can fall back to copying."""
        exdev = OSError(errno.EXDEV, "device")
        with (
            mock.patch("os.link", side_effect=exdev),
            self.assertRaises(OSError) as caught,
        ):
            transfer._rename_exclusive(self.a, self.b)
        self.assertEqual(caught.exception.errno, errno.EXDEV)

    @unittest.skipIf(os.name == "nt", "POSIX rename semantics")
    def test_a_name_that_cannot_be_removed_leaves_no_second_name(self):
        """If unlinking the old name fails, the new link is removed again."""
        real = os.unlink

        def unlink(path, *args, **kwargs):
            if path == self.a:
                raise PermissionError(errno.EACCES, "in use", path)
            return real(path, *args, **kwargs)

        with (
            mock.patch("os.unlink", unlink),
            self.assertRaises(PermissionError),
        ):
            transfer._rename_exclusive(self.a, self.b)
        self.assertEqual(_listing(self.dst), [])
        self.assertEqual(_content(self.src, "plate", 1), "plate 1")

    def test_windows_uses_a_plain_rename(self):
        """os.rename already refuses to replace there."""
        with mock.patch.object(transfer.os, "name", "nt"):
            transfer._rename_exclusive(self.a, self.b)
        self.assertEqual(_content(self.dst, "plate", 1), "plate 1")

    def test_a_failed_replace_cleans_up_the_temporary_file(self):
        """An overwriting copy leaves neither a temp file nor damage."""
        with open(self.b, "w") as handle:
            handle.write("old")
        plan = transfer.plan_copy(
            _seq(self.src, "plate", [1]), self.dst, overwrite=True
        )
        with (
            mock.patch(
                "os.replace", side_effect=PermissionError(errno.EACCES, "no")
            ),
            self.assertRaises(transfer.TransferError),
        ):
            plan.execute()
        self.assertEqual(_listing(self.dst), ["plate.0001.exr"])
        self.assertEqual(_content(self.dst, "plate", 1), "old")


class TestReviewedEdgeCases(_TempDirs):
    """Found by code review: links, directories, long names."""

    def setUp(self):
        """Three frames to transfer."""
        super().setUp()
        _make(self.src, "plate", [1, 2, 3])
        self.fseq = _seq(self.src, "plate", [1, 2, 3])

    def _can_link(self):
        """Skip unless hard links work here."""
        try:
            os.link(_name(self.src, "plate", 1), os.path.join(self.root, "z"))
        except (OSError, NotImplementedError):
            self.skipTest("hard links are not available")

    def test_overwriting_a_hard_link_of_the_source_completes_the_move(self):
        """rename() is a no-op for two names of one file; the move is not."""
        self._can_link()
        os.link(_name(self.src, "plate", 2), _name(self.dst, "plate", 2))
        transfer.plan_move(self.fseq, self.dst, overwrite=True).execute()
        self.assertEqual(_listing(self.src), [])
        self.assertEqual(len(_listing(self.dst)), 3)
        self.assertEqual(_content(self.dst, "plate", 2), "plate 2")

    def test_a_blocked_parent_directory_is_a_transfer_error(self):
        """parents=True under a plain file: reported, nothing left behind."""
        with open(os.path.join(self.dst, "blocker"), "w") as handle:
            handle.write("a file")
        target = os.path.join(self.dst, "blocker", "deeper")
        plan = transfer.plan_copy(self.fseq, target, parents=True)
        with self.assertRaises(transfer.TransferError) as caught:
            plan.execute()
        error = caught.exception
        self.assertEqual((error.done, error.failed[1]), ([], target))
        self.assertTrue(error.rolled_back)
        self.assertEqual(_listing(self.dst), ["blocker"])
        self.assertEqual(len(_listing(self.src)), 3)

    def test_directories_made_before_a_failure_are_removed(self):
        """Creating a/b/c fails at c: a and b go away again."""
        target = os.path.join(self.dst, "a", "b", "c")
        real = os.mkdir
        calls = []

        def mkdir(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 3:
                raise PermissionError(errno.EACCES, "denied", path)
            return real(path, *args, **kwargs)

        plan = transfer.plan_copy(self.fseq, target, parents=True)
        with (
            mock.patch("os.mkdir", mkdir),
            self.assertRaises(transfer.TransferError),
        ):
            plan.execute()
        self.assertEqual(_listing(self.dst), [])

    def test_a_directory_made_by_someone_else_meanwhile_is_fine(self):
        """mkdir loses a race: the directory is there, so carry on."""
        target = os.path.join(self.dst, "raced")
        real = os.mkdir

        def mkdir(path, *args, **kwargs):
            real(path, *args, **kwargs)
            raise FileExistsError(errno.EEXIST, "exists", path)

        plan = transfer.plan_copy(self.fseq, target, parents=True)
        with mock.patch("os.mkdir", mkdir):
            plan.execute()
        self.assertEqual(len(_listing(target)), 3)

    @unittest.skipIf(os.name == "nt", "path length limits differ")
    def test_a_long_destination_name_can_be_overwritten(self):
        """The temporary file must not be longer than the name it replaces."""
        base = "x" * 235  # 244 characters with the frame and extension
        long_src = os.path.join(self.root, "a")
        long_dst = os.path.join(self.root, "b")
        os.mkdir(long_src)
        os.mkdir(long_dst)
        _make(long_src, base, [1])
        _make(long_dst, base, [1])
        plan = transfer.plan_copy(
            _seq(long_src, base, [1]), long_dst, overwrite=True
        )
        plan.execute()
        self.assertEqual(len(_listing(long_dst)), 1)
        self.assertEqual(_content(long_dst, base, 1), f"{base} 1")

    def test_aliases_are_only_worked_out_when_needed(self):
        """Nothing exists at the destinations: no alias lookups at all."""
        with mock.patch.object(transfer, "_alias", side_effect=AssertionError):
            plan = transfer.plan_move(self.fseq, self.dst)
        self.assertEqual(plan.problems, [])
