"""Edge cases of the frame storage, membership, pickling and the CLI."""

import array
import contextlib
import io
import os
import pathlib
import pickle
import random
import tempfile
import unittest
from unittest import mock

import seqparse
from seqparse import files, sequences
from seqparse.cli import seqls

BIG = 2**70  # too big for the compact 64-bit frame store


class TestOversizedFrames(unittest.TestCase):
    """Frames beyond 64 bits fall back to a list wherever they arrive."""

    def test_in_a_frame_sequence_string(self):
        """Parsing a string with a huge frame."""
        seq = sequences.FrameSequence(f"1-3,{BIG}")
        self.assertEqual(str(seq), f"1-3,{BIG}")
        self.assertIn(BIG, seq)

    def test_in_a_bulk_set(self):
        """Building from a set holding a huge frame."""
        self.assertEqual(str(sequences.FrameSequence({BIG, 1})), f"1,{BIG}")

    def test_in_a_bulk_range_after_small_frames(self):
        """A huge range queued after small frames."""
        seq = sequences.FrameSequence([1])
        seq.update([5])
        seq.add(range(BIG, BIG + 2))  # one bulk add
        seq.add(2)
        self.assertEqual(str(seq), f"1,2,5,{BIG},{BIG + 1}")


class TestUncommonInputs(unittest.TestCase):
    """Inputs that skip the fast paths."""

    def test_scalar_frames(self):
        """A single int or a non-int number is one frame."""
        self.assertEqual(str(sequences.FrameSequence(7)), "7")
        seq = sequences.FrameSequence([1])
        seq.add(3.0)
        self.assertEqual(str(seq), "1,3")

    def test_compact_array_input(self):
        """An array of 64-bit ints is taken as frame numbers."""
        self.assertEqual(
            str(sequences.FrameSequence(array.array("q", [5, 3, 4]))), "3-5"
        )

    def test_adding_a_file_sequence_to_frames(self):
        """FileSequence iterates file names, which aren't frames."""
        seq = sequences.FrameSequence([1], pad=4)
        file_seq = sequences.FileSequence(
            name="a", ext="exr", frames=[2], pad=4
        )
        with self.assertRaises(ValueError):
            seq.add(file_seq)

    def test_is_dirty(self):
        """is_dirty reports whether the output needs recalculating."""
        seq = sequences.FrameSequence([1])
        self.assertTrue(seq.is_dirty)
        str(seq)
        self.assertFalse(seq.is_dirty)
        seq.add(2)
        self.assertTrue(seq.is_dirty)


class TestFileSequenceMerging(unittest.TestCase):
    """FileSequence.update() with sequences of a different pad."""

    def test_unpadded_frames_merge(self):
        """Frames without leading zeros are valid at any pad."""
        fseq = sequences.FileSequence(name="a", ext="exr", frames=[1000], pad=4)
        fseq.update(
            sequences.FileSequence(name="a", ext="exr", frames=[1234], pad=3)
        )
        self.assertEqual(str(fseq), "a.1000,1234.exr")

    def test_conflicting_padding_raises(self):
        """Zero-padded frames of another width are rejected."""
        fseq = sequences.FileSequence(name="a", ext="exr", frames=[1, 2], pad=4)
        other = sequences.FileSequence(name="a", ext="exr", frames=[5], pad=2)
        with self.assertRaises(sequences.SeqparsePadError):
            fseq.update(other)


class TestFileNameMembership(unittest.TestCase):
    """Membership tests that aren't plain member file names."""

    def setUp(self):
        """A one-frame sequence."""
        self.fseq = sequences.FileSequence(
            name="a", ext="exr", frames=[1], pad=4
        )

    def test_non_string_items(self):
        """Only ints and digit strings are frames; other objects aren't."""
        self.assertIn(1, self.fseq)
        self.assertNotIn(1.0, self.fseq)
        self.assertNotIn(object(), self.fseq)

    def test_malformed_names(self):
        """Too short to hold a frame, or a non-digit frame."""
        self.assertNotIn("a.exr", self.fseq)
        self.assertNotIn("a.abcd.exr", self.fseq)
        self.assertIn("a.0001.exr", self.fseq)


class TestPickling(unittest.TestCase):
    """Current-version pickles round-trip."""

    def test_file(self):
        """A File with cached stats."""
        file = files.File("/r/a.txt", (0,) * 6 + (7,) + (0,) * 3)
        clone = pickle.loads(pickle.dumps(file))
        self.assertEqual((clone.full_name, clone.size), ("/r/a.txt", 7))


class TestSeqlsPrinting(unittest.TestCase):
    """seqls prints (rather than returns) its output outside debug mode."""

    def _run(self, *argv):
        """Run seqls, returning what it printed."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = seqls.main(seqls.parse_args(list(argv)))
        self.assertIsNone(result)
        return buffer.getvalue()

    def test_version(self):
        """--version prints the version."""
        self.assertEqual(
            self._run("--version"), seqparse.get_version(pretty=True) + "\n"
        )

    def test_listing(self):
        """A scan prints a blank line, then one line per item."""
        with tempfile.TemporaryDirectory() as root:
            for frame in (1, 2, 3):
                with open(os.path.join(root, f"a.{frame:04d}.exr"), "w"):
                    pass
            printed = self._run(root)
        expected = os.path.join(os.path.abspath(root), "a.0001-0003.exr")
        self.assertEqual(printed, f"\n{expected}\n")


class TestMembershipOfNonFrames(unittest.TestCase):
    """`x in sequence` answers False for numbers that are not frames."""

    def test_nan_and_infinity(self):
        """They used to raise ValueError and OverflowError."""
        for container in (
            sequences.FrameSequence([1, 2, 3]),
            sequences.FrameChunk(1, 5),
            sequences.FileSequence(name="x", ext="exr", frames=[1, 2]),
        ):
            for value in (float("nan"), float("inf"), float("-inf"), 1.5):
                with self.subTest(
                    container=type(container).__name__, value=value
                ):
                    self.assertNotIn(value, container)

    def test_a_bad_frame_string_is_still_an_error(self):
        """Only numbers are quietly not-members."""
        with self.assertRaises(ValueError):
            _ = "not a frame" in sequences.FrameSequence([1])

    def test_discard_agrees_with_membership(self):
        """The same inputs are ignored."""
        seq = sequences.FrameSequence([1, 2, 3])
        for value in (float("nan"), float("inf"), 1.5):
            seq.discard(value)
        self.assertEqual(str(seq), "1-3")


class TestPathLikeNames(unittest.TestCase):
    """A path-like name means its text, exactly like the str (issue review)."""

    def test_a_path_holding_a_sequence_string_parses_like_the_str(self):
        """It used to give no frames and no extension, silently."""
        for text in ("/a/b/foo.1-5.exr", "foo.0001-0003.exr"):
            with self.subTest(text=text):
                from_str = sequences.FileSequence(name=text)
                from_path = sequences.FileSequence(name=pathlib.Path(text))
                self.assertEqual(
                    (from_path.name, from_path.ext, list(from_path.frames)),
                    (from_str.name, from_str.ext, list(from_str.frames)),
                )
                self.assertGreater(len(from_path), 0)

    def test_a_path_name_with_frames_given(self):
        """The usual way: a path for the name, frames and extension apart."""
        fseq = sequences.FileSequence(
            name=pathlib.Path("shots") / "plate",
            ext="exr",
            frames=[1, 2],
            pad=4,
        )
        self.assertEqual(
            str(fseq), os.path.join("shots", "plate.0001,0002.exr")
        )

    def test_the_name_setter_takes_paths_and_directory_entries(self):
        """str() of a DirEntry would be its repr."""

        class Entry:
            def __fspath__(self):
                return os.path.join("x", "y", "plate")

        for value in (pathlib.Path("x") / "y" / "plate", Entry()):
            with self.subTest(value=type(value).__name__):
                fseq = sequences.FileSequence(frames=[1], ext="exr")
                fseq.name = value
                self.assertEqual(
                    (fseq.name, fseq.path), ("plate", os.path.join("x", "y"))
                )


def _stat(size, mtime, ctime):
    """A stat_result with the given size and times."""
    return os.stat_result((0o100644, 1, 2, 1, 0, 0, size, 1, mtime, ctime))


class TestAggregateStats(unittest.TestCase):
    """size, mtime and ctime follow cache_stat without a full recompute."""

    def make(self, frames):
        """A sequence of the given frames."""
        return sequences.FileSequence(name="x", ext="exr", frames=frames, pad=4)

    def test_reading_after_every_cache_stat_does_not_recompute(self):
        """It used to be quadratic: a full recompute per call."""
        real = sequences.FileSequence._aggregate_stats
        seq = self.make(range(1, 201))
        with mock.patch.object(
            sequences.FileSequence,
            "_aggregate_stats",
            autospec=True,
            side_effect=real,
        ) as aggregate:
            for number in range(1, 201):
                seq.cache_stat(number, _stat(number, number, number * 2))
                self.assertEqual(seq.size, number * (number + 1) // 2)
        self.assertLessEqual(aggregate.call_count, 1)
        self.assertEqual((seq.mtime, seq.ctime), (200, 400))

    def test_the_numbers_agree_with_a_full_recompute(self):
        """Seeded random caching, replacing, discarding and adding."""
        rng = random.Random(4)
        for _ in range(60):
            frames = rng.sample(range(40), rng.randint(1, 15))
            seq = self.make(frames)
            cached = {}
            for _ in range(rng.randint(1, 30)):
                number = rng.choice(range(45))  # some are not members
                info = _stat(
                    rng.randint(0, 99), rng.randint(0, 99), rng.randint(0, 99)
                )
                seq.cache_stat(number, info)
                cached[number] = info
                action = rng.random()
                if action < 0.15:
                    seq.discard(number)
                    cached.pop(number, None)
                elif action < 0.3:
                    seq.add(rng.choice(range(45)))
                if rng.random() < 0.5:
                    _ = seq.size  # read in between, as a caller may
            members = {n: i for n, i in cached.items() if n in seq}
            expected = (
                sum(i.st_size for i in members.values()) if members else None,
                max((i.st_mtime for i in members.values()), default=None),
                max((i.st_ctime for i in members.values()), default=None),
            )
            self.assertEqual(
                (seq.size, seq.mtime, seq.ctime), expected, (frames, cached)
            )

    def test_a_replaced_stat_can_lower_the_newest_time(self):
        """The maximum is not a running value once a stat is replaced."""
        seq = self.make([1, 2])
        seq.cache_stat(1, _stat(1, 100, 100))
        seq.cache_stat(2, _stat(1, 50, 50))
        self.assertEqual(seq.mtime, 100)
        seq.cache_stat(1, _stat(1, 10, 10))
        self.assertEqual((seq.mtime, seq.ctime), (50, 50))

    def test_a_stat_cached_before_its_frame_exists_counts_once_added(self):
        """Not a member yet: not counted until it is."""
        seq = self.make([1])
        seq.cache_stat(9, _stat(7, 5, 5))
        self.assertIsNone(seq.size)
        seq.add(9)
        self.assertEqual(seq.size, 7)
