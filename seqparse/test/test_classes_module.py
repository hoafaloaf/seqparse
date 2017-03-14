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
            print "o %s -> %s (%r, %d frames)" % (bit, chunk, chunk,
                                                  len(chunk))

        print "\n  BAD CHUNKS\n  -------------"
        for bit in self.bad_bits:
            try:
                chunk = FrameChunk(*bit)
            except ValueError as error:
                print "o ERROR: %s --> %s" % (bit, error)
