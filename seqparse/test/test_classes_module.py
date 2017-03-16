"""Test the individual classes."""

# Standard Libraries
import unittest

from seqparse.classes import FrameChunk


###############################################################################
# class: TestFrameSequences


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
        """Test chunk length (number of included frames)."""
        print "\n  GOOD CHUNKS\n  --------------"
        for bit in self.good_bits:
            chunk = FrameChunk(*bit[:-1])
            self.assertEqual(len(chunk), bit[-1])
            print "  o %s -> %s (%r, %d frames)" % (bit, chunk, chunk,
                                                    len(chunk))

        print "\n  BAD CHUNKS\n  -------------"
        for bit in self.bad_bits:
            try:
                chunk = FrameChunk(*bit)
            except ValueError as error:
                print "  o ERROR: %s --> %s" % (bit, error)

    def test_frame_containment(self):
        """Test if a frame is contained by a chunk."""
        chunk = FrameChunk(first=1, last=5, step=1, pad=4)
        for frame in xrange(1, 6):
            self.assertIn(frame, chunk)
            self.assertIn("%04d" % frame, chunk)

        for frame in (0, 6):
            self.assertNotIn(frame, chunk)
            self.assertNotIn("%02d" % frame, chunk)
            self.assertNotIn("%04d" % frame, chunk)

        chunk = FrameChunk(first=1, last=7, step=2, pad=4)
        for frame in xrange(1, 8, 2):
            self.assertIn(frame, chunk)
            self.assertIn("%04d" % frame, chunk)

        for frame in xrange(0, 9, 2):
            self.assertNotIn(frame, chunk)
            self.assertNotIn("%02d" % frame, chunk)
            self.assertNotIn("%04d" % frame, chunk)

        chunk = FrameChunk(first=1, last=10, step=1, pad=1)
        for frame in xrange(1, 11):
            self.assertIn(frame, chunk)
            self.assertIn(str(frame), chunk)

        for frame in xrange(1, 10):
            self.assertNotIn("%02d" % frame, chunk)

        for frame in (0, 11):
            self.assertNotIn(frame, chunk)
            self.assertNotIn(str(frame), chunk)
            self.assertNotIn("%02d" % frame, chunk)
