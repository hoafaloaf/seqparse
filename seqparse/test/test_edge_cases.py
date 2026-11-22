"""Edge cases of the frame storage, membership, pickling and the CLI."""

import array
import contextlib
import io
import os
import pickle
import tempfile
import unittest

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
