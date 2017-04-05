"""Test the FrameChunk class."""

# "Future" Libraries
from __future__ import print_function

# Standard Libraries
import unittest

from ..sequences import FrameChunk


###############################################################################
# class: TestFrameChunks


class TestFrameChunks(unittest.TestCase):
    """Test basic functionality on the FrameChunk class."""

    # First four arguments are fed to FrameChunk instances, the last is the
    # expected length (ie, number of frames) of the chunk.
    good_bits = (("0001", None, 1, 1, 1), ("0001", "0005", 1, 1, 5),
                 ("0001", "0005", 2, 1, 3), ("0001", "0005", 2, 2, 3),
                 ("0001", "0005", 3, 1, 2), ("0001", "0005", 3, 2, 2))
    bad_bits = (("0005", "0001", None, 1), )

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_chunk_length(self):
        """FrameChunk: Test chunk length (number of included frames)."""
        print("\n  GOOD CHUNKS\n  --------------")
        for bit in self.good_bits:
            chunk = FrameChunk(*bit[:-1])
            self.assertEqual(len(chunk), bit[-1])
            print("  o {} -> {} ({!r}, {:d} frames)".format(bit, chunk, chunk,
                                                            len(chunk)))

        print("\n  BAD CHUNKS\n  -------------")
        for bit in self.bad_bits:
            try:
                chunk = FrameChunk(*bit)

            except ValueError as error:
                print("  o EXPECTED ERROR: {} --> {}".format(bit, error))
                assert True

    def test_containment(self):
        """FrameChunk: Test if a frame is contained by a chunk."""
        chunk = FrameChunk(first=1, last=5, step=1, pad=4)
        for frame in xrange(1, 6):
            self.assertIn(frame, chunk)
            self.assertIn("{:04d}".format(frame), chunk)

        for frame in (0, 6):
            self.assertNotIn(frame, chunk)
            self.assertNotIn("{:02d}".format(frame), chunk)
            self.assertNotIn("{:04d}".format(frame), chunk)

        chunk = FrameChunk(first=1, last=7, step=2, pad=4)
        for frame in xrange(1, 8, 2):
            self.assertIn(frame, chunk)
            self.assertIn("{:04d}".format(frame), chunk)

        for frame in xrange(0, 9, 2):
            self.assertNotIn(frame, chunk)
            self.assertNotIn("{:02d}".format(frame), chunk)
            self.assertNotIn("{:04d}".format(frame), chunk)

        chunk = FrameChunk(first=1, last=10, step=1, pad=1)
        for frame in xrange(1, 11):
            self.assertIn(frame, chunk)
            self.assertIn(str(frame), chunk)

        for frame in xrange(1, 10):
            self.assertNotIn("{:02d}".format(frame), chunk)

        for frame in (0, 11):
            self.assertNotIn(frame, chunk)
            self.assertNotIn(str(frame), chunk)
            self.assertNotIn("{:02d}".format(frame), chunk)

    def test_iteration(self):
        """FrameChunk: Test iteration over an instance."""
        chunk = FrameChunk(first=1, last=5, step=1, pad=4)
        frames = ["{:04d}".format(x) for x in xrange(1, 6)]

        self.assertEqual(set(frames), set(chunk))

        print("\n\n  INPUT FRAMES\n  ------------")
        print(" ", frames)

        print("\n\n  ITERATION\n  ---------")
        print("  o forward: ", ", ".join(x for x in chunk))
        print("  o backward:", ", ".join(x for x in reversed(chunk)))

        chunk = FrameChunk(first=1, last=20, step=2, pad=1)
        frames = [str(x) for x in xrange(1, 21, 2)]

        self.assertEqual(set(frames), set(chunk))

        print("\n\n  INPUT FRAMES\n  ------------")
        print(" ", frames)

        print("\n\n  ITERATION\n  ---------")
        print("  o forward: ", ", ".join(x for x in chunk))
        print("  o backward:", ", ".join(x for x in reversed(chunk)))

    def test_inversion(self):
        """FrameChunk: Test frame inversion (ie, report missing frames)."""
        chunk = FrameChunk(first=1, last=11, step=2, pad=4)
        expected = FrameChunk(first=2, last=10, step=2, pad=4)

        print("\n\n  SEQUENCE\n  --------")
        print("  input frames:   ", chunk)
        print("  expected frames:", expected)
        inverted = chunk.invert()
        print("  returned frames:", inverted)

        self.assertEqual(str(inverted), str(expected))

        chunk = FrameChunk(first=10, pad=4)
        expected = ""

        print("\n  SINGLE FRAME\n  -----------")
        print("  input frames:   ", chunk)
        print("  expected frames:", expected)
        inverted = chunk.invert()
        print("  returned frames:", inverted)
        print("")

        self.assertEqual(str(inverted), str(expected))

    def test_equality(self):
        """FrameChunk: Test the equality of instances."""
        chunk1 = FrameChunk(first=1, last=10, pad=4)
        chunk2 = FrameChunk(first="1", last="10", pad=4)
        chunk3 = FrameChunk(first=1, last=10, pad=4)
        chunk4 = FrameChunk(first=1, last=10, pad=3)
        chunk5 = FrameChunk(first="1", last="10", pad=3)
        self.assertEqual(chunk1, chunk2)
        self.assertEqual(chunk1, chunk3)
        self.assertNotEqual(chunk1, chunk4)
        self.assertNotEqual(chunk1, chunk5)
        self.assertNotEqual(chunk2, chunk4)

        self.assertNotEqual(chunk1, "0001-0010")
