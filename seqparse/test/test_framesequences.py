"""Test the FrameSequence class."""

# "Future" Libraries
from __future__ import print_function

# Standard Libraries
import os
import unittest

# Third Party Libraries
from builtins import range
from future.utils import lrange

from ..sequences import (FileSequence, FrameChunk, FrameSequence,
                         SeqparsePadException)

###############################################################################
# class: TestFrameSequences


class TestFrameSequences(unittest.TestCase):
    """Test basic functionality on the FrameSequence class."""

    _test_ext = "exr"
    _test_name = "cat"
    _test_path = "/pretty/kitty".replace("/", os.sep)

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_initialization(self):
        """FrameSequence: Test initialization of an instance."""
        # Tuples indicate "frames" and "pad"; complex data types don't need a
        # specified pad.
        data = [("wow", None, 1), ("4", "4", 1), (3, "3", 1),
                (FrameChunk(first=2, pad=4), "0002", None),
                (FrameSequence(lrange(30, 41, 2), pad=2), "30-40x2", None)]

        print("\n\n  INPUT ARGUMENTS\n  ---------------")

        for datum in data:
            iterable, expected, pad = datum

            print("  o iterable: {!r}".format(iterable), end=' ')
            if pad is not None:
                print("pad: {:d}".format(pad))
            else:
                print("")

            try:
                seq = FrameSequence(frames=iterable, pad=pad)
            except ValueError as error:
                print(
                    "    - EXPECTED ERROR: {} --> {}".format(iterable, error))
            else:
                print("    - GOOD: {}".format(seq))
                self.assertEqual(str(seq), expected)

    def test_basic_containment(self):
        """FrameSequence: Test basic containment of sequences."""
        chunk1 = FrameChunk(first=1, last=11, step=1, pad=1)
        frames1 = [str(x) for x in range(1, 12)]
        str_frames1 = "1-11"

        seq = FrameSequence(frames1, pad=1)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))
        self.assertEqual(str_frames1, str(seq))

        seq = FrameSequence()
        seq.pad = 1
        seq.add(frames1)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))
        self.assertEqual(str_frames1, str(seq))

        seq = FrameSequence()
        seq.pad = 1
        for frame in frames1:
            seq.add(frame)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))
        self.assertEqual(str_frames1, str(seq))

        seq = FrameSequence(str_frames1)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))
        self.assertEqual(str_frames1, str(seq))

        for frame in range(1, 12):
            self.assertIn(frame, seq)
            self.assertIn(str(frame), seq)
            self.assertNotIn("{:04d}".format(frame), seq)

        self.assertNotIn(13, seq)
        self.assertNotIn("13", seq)
        self.assertNotIn("0013", seq)

        seq1 = FrameSequence(chunk1)
        self.assertEqual(str(chunk1), str(seq1))

        seq2 = FrameSequence(seq1)
        self.assertEqual(str(seq1), str(seq2))

        # Empty FrameSequence ...
        self.assertEqual(str(FrameSequence()), "")

    def test_complex_containment(self):
        """FrameSequence: Test containment of complex sequences."""
        chunk2 = FrameChunk(first=1, last=11, step=1, pad=4)
        frames2 = ["{:04d}".format(x) for x in range(1, 12)]
        str_frames2 = "0001-0011"
        chunk3 = FrameChunk(first=91, last=101, step=2, pad=4)
        frames3 = ["{:04d}".format(x) for x in range(91, 103, 2)]
        str_frames3 = "0091-0101x2"

        seq = FrameSequence(frames2, pad=4)
        self.assertEqual(str(chunk2), str(seq))
        self.assertEqual(set(chunk2), set(seq))
        self.assertEqual(set(frames2), set(seq))
        self.assertEqual(str_frames2, str(seq))

        seq = FrameSequence(str_frames2)
        self.assertEqual(str(chunk2), str(seq))
        self.assertEqual(set(chunk2), set(seq))
        self.assertEqual(set(frames2), set(seq))
        self.assertEqual(str_frames2, str(seq))

        seq = FrameSequence(frames3, pad=4)
        self.assertEqual(str(chunk3), str(seq))
        self.assertEqual(set(chunk3), set(seq))
        self.assertEqual(set(frames3), set(seq))
        self.assertEqual(str_frames3, str(seq))

        seq = FrameSequence(str_frames3)
        self.assertEqual(str(chunk3), str(seq))
        self.assertEqual(set(chunk3), set(seq))
        self.assertEqual(set(frames3), set(seq))
        self.assertEqual(str_frames3, str(seq))

    def test_frame_add(self):
        """FrameSequence: Test the addition of frames of various types."""
        chunk3 = FrameChunk(first=91, last=102, step=2, pad=4)
        frames3 = ["{:04d}".format(x) for x in range(91, 103, 2)]

        seq = FrameSequence(frames3, pad=4)
        self.assertEqual(str(chunk3), str(seq))
        self.assertEqual(set(chunk3), set(seq))
        self.assertEqual(set(frames3), set(seq))

        # Add additional data types.
        data = [
            "wow", "05", "4", 3, "010-020x2", "010,,020", "0010,,0020",
            FrameChunk(first=2, pad=4),
            FrameChunk(first=10, last=20, step=2, pad=2),
            FrameChunk(first=10, last=20, step=2, pad=4),
            FrameSequence([1], pad=4),
            FrameSequence([x for x in range(30, 41, 2)], pad=2),
            FrameSequence([x for x in range(30, 41, 2)], pad=4)
        ]

        print("")
        for item in data:
            print("  o Testing {}: {}".format(type(item).__name__, item))

            try:
                seq.add(item)
            except ValueError as error:
                print("    - EXPECTED ERROR: {} --> {}".format(item, error))
                assert True
            except SeqparsePadException as error:
                print("    - EXPECTED ERROR: {} --> {}".format(item, error))

        self.assertEqual(
            str(seq), "0001-0004,0010-0020x2,0030-0040x2,0091-0101x2")

    def test_setlike_methods(self):
        """FrameSequence: Test set-like methods."""
        frames = [1, 2, 3, 4, 11, 12, 13, 14]
        pad_frames = ["{:04d}".format(x) for x in frames]

        seq = FrameSequence(frames, pad=4)
        self.assertEqual(set(pad_frames), set(seq))

        seq = FrameSequence(frames, pad=4)
        seq.discard(pad_frames[-1])
        self.assertEqual(set(pad_frames[:-1]), set(seq))

        seq = FrameSequence(frames, pad=4)
        pad_frames2 = ["{:04d}".format(x) for x in [21, 22, 23, 24]]
        seq.update(pad_frames2)
        self.assertEqual(set(pad_frames + pad_frames2), set(seq))

        seq = FrameSequence(frames, pad=4)
        with self.assertRaises(SeqparsePadException):
            seq.discard("014")

        # Not really a set-like method, but I need to test it ...
        seq = FrameSequence(frames, pad=1)
        self.assertFalse(seq.is_padded)
        seq = FrameSequence(frames, pad=4)
        self.assertTrue(seq.is_padded)

    def test_iteration(self):
        """FrameSequence: Test iteration over an instance."""
        frames = ["{:04d}".format(x) for x in range(1, 6)]
        seq = FrameSequence(frames, pad=4)

        print("\n\n  INPUT FRAMES\n  ------------")
        print(" ", frames)

        print("\n\n  ITERATION\n  ---------")
        print("  o forward: ", ", ".join([x for x in seq]))
        print("  o backward:", ", ".join(list(reversed(seq))))

        self.assertEqual(set(frames), set(seq))

        frames = [str(x) for x in range(1, 21, 2)]
        frames += [str(x) for x in range(100, 105)]
        seq = FrameSequence(frames, pad=1)

        print("\n\n  INPUT FRAMES\n  ------------")
        print(" ", frames)

        print("\n\n  ITERATION\n  ---------")
        print("  o forward: ", ", ".join([x for x in seq]))
        print("  o backward:", ", ".join(list(reversed(seq))))

        self.assertEqual(set(frames), set(seq))

    def test_inversion(self):
        """FrameSequence: Test frame inversion (ie, report missing frames)."""
        chunk = FrameChunk(first=1, last=11, step=2, pad=4)
        seq = FrameSequence(chunk)
        expected = FrameChunk(first=2, last=10, step=2, pad=4)
        inverted = seq.invert()

        print("\n\n  SEQUENCE\n  --------")
        print("  input frames:   ", seq)
        print("  expected frames:", expected)
        print("  returned frames:", inverted)

        self.assertEqual(str(inverted), str(expected))

        chunk1 = FrameChunk(first=1, last=9, step=2, pad=4)
        chunk2 = FrameChunk(first=10, last=20, step=5, pad=4)
        seq = FrameSequence(chunk1)
        seq.add(chunk2)
        seq.add("0021")

        expected = FrameSequence(pad=4)
        expected.add(chunk1.invert())
        expected.add(chunk2.invert())
        inverted = seq.invert()

        print("\n  COMPLEX FRAME\n  ------------")
        print("  input frames:   ", seq)
        print("  expected frames:", expected)
        print("  returned frames:", inverted)
        print("")

        self.assertEqual(str(inverted), str(expected))

    def test_equality(self):
        """FrameSequence: Test the equality of instances."""
        seq1 = FrameSequence(lrange(1, 11), pad=4)
        seq2 = FrameSequence(lrange(1, 11), pad=4)
        seq3 = FrameSequence(lrange(1, 11), pad=3)
        seq4 = FrameSequence(lrange(1, 10), pad=4)
        seq5 = FrameSequence("0001-0010")
        seq6 = FrameSequence("0001-0010")
        seq7 = FrameSequence("001-010")
        seq8 = FrameSequence("0001-0009")

        self.assertEqual(seq1, seq2)
        self.assertNotEqual(seq1, seq3)
        self.assertNotEqual(seq1, seq4)
        self.assertEqual(seq1, seq5)
        self.assertEqual(seq3, seq7)
        self.assertEqual(seq4, seq8)
        self.assertEqual(seq5, seq6)
        self.assertNotEqual(seq5, seq7)
        self.assertNotEqual(seq5, seq8)

        file_path = os.path.join(self._test_path, self._test_name)
        fseq1 = FileSequence(
            name=file_path, ext=self._test_ext, frames=lrange(1, 11), pad=4)

        self.assertNotEqual(seq1, fseq1)
