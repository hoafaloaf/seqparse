"""Test the FrameSequence class."""

# Standard Libraries
import unittest

from seqparse.classes import FrameChunk, FrameSequence, SeqparsePadException


###############################################################################
# class: TestFrameSequences


class TestFrameSequences(unittest.TestCase):
    """Test basic functionality on the FrameSequence class."""

    def setUp(self):
        """Set up the test instance."""
        pass

    def test_simple_containment(self):
        """FrameSequence: Test if frames are contained by a sequence."""
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

        for frame in xrange(1, 12):
            self.assertIn(frame, seq)
            self.assertIn(str(frame), seq)
            self.assertNotIn("%04d" % frame, seq)

        self.assertNotIn(13, seq)
        self.assertNotIn("13", seq)
        self.assertNotIn("0013", seq)

        seq = FrameSequence(frames2, pad=4)
        self.assertEqual(str(chunk2), str(seq))
        self.assertEqual(set(chunk2), set(seq))
        self.assertEqual(set(frames2), set(seq))

        seq = FrameSequence(frames3, pad=4)
        self.assertEqual(str(chunk3), str(seq))
        self.assertEqual(set(chunk3), set(seq))
        self.assertEqual(set(frames3), set(seq))

        seq1 = FrameSequence(chunk1)
        self.assertEqual(str(chunk1), str(seq1))

        seq2 = FrameSequence(seq1)
        self.assertEqual(str(seq1), str(seq2))

        # Empty FrameSequence ...
        self.assertEqual(str(FrameSequence()), "")

    def test_frame_add(self):
        """FrameSequence: Test the addition of frames of various types."""
        chunk3 = FrameChunk(first=91, last=102, step=2, pad=4)
        frames3 = ["%04d" % x for x in xrange(91, 103, 2)]

        seq = FrameSequence(frames3, pad=4)
        self.assertEqual(str(chunk3), str(seq))
        self.assertEqual(set(chunk3), set(seq))
        self.assertEqual(set(frames3), set(seq))

        # Add additional data types.
        data = [
            "wow", "05", "4", 3, FrameChunk(first=2, pad=4),
            FrameChunk(first=10, last=20, step=2, pad=2),
            FrameChunk(first=10, last=20, step=2, pad=4),
            FrameSequence([1], pad=4),
            FrameSequence([x for x in xrange(30, 41, 2)], pad=2),
            FrameSequence([x for x in xrange(30, 41, 2)], pad=4)
        ]

        print
        for item in data:
            print "  o Testing %s: %s" % (type(item).__name__, item)

            try:
                seq.add(item)
            except ValueError as error:
                print "    - EXPECTED ERROR: %s --> %s" % (item, error)
                assert True
            except SeqparsePadException as error:
                print "    - EXPECTED ERROR: %s --> %s" % (item, error)

        self.assertEqual(
            str(seq), "0001-0004,0010-0020x2,0030-0040x2,0091-0101x2")

    def test_setlike_methods(self):
        """FrameSequence: Test set-like methods."""
