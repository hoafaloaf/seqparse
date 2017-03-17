"""Test the FrameSequence class."""

# Standard Libraries
import unittest

from seqparse.classes import FrameChunk, FrameSequence


###############################################################################
# class: TestFrameSequences


class TestFrameSequences(unittest.TestCase):
    """Test basic functionality on the FrameSequence class."""

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_frame_containment(self):
        """Test if frames are contained by a sequence."""
        chunk1 = FrameChunk(first=1, last=11, step=1, pad=1)
        frames1 = [str(x) for x in xrange(1, 12)]
        chunk2 = FrameChunk(first=1, last=11, step=1, pad=4)
        frames2 = ["%04d" % x for x in xrange(1, 12)]
        chunk3 = FrameChunk(first=91, last=102, step=2, pad=4)
        frames3 = ["%04d" % x for x in xrange(91, 103, 2)]

        seq = FrameSequence(frames1, pad=1)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))

        seq = FrameSequence()
        seq.pad = 1
        seq.add(frames1)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))

        seq = FrameSequence()
        seq.pad = 1
        for frame in frames1:
            seq.add(frame)
        self.assertEqual(str(chunk1), str(seq))
        self.assertEqual(set(chunk1), set(seq))
        self.assertEqual(set(frames1), set(seq))

        seq = FrameSequence(frames2, pad=4)
        self.assertEqual(str(chunk2), str(seq))
        self.assertEqual(set(chunk2), set(seq))
        self.assertEqual(set(frames2), set(seq))

        seq = FrameSequence(frames3, pad=4)
        self.assertEqual(str(chunk3), str(seq))
        self.assertEqual(set(chunk3), set(seq))
        self.assertEqual(set(frames3), set(seq))
