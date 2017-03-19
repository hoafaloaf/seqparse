"""Test the FrameSequence class."""

# Standard Libraries
import os
import unittest

from seqparse.sequences import FileSequence, FrameChunk, FrameSequence


###############################################################################
# class: TestFrameSequences


class TestFileSequences(unittest.TestCase):
    """Test basic functionality on the FileSequence class."""

    _test_ext = "exr"
    _test_name = "cat"
    _test_path = "/pretty/kitty"

    def setUp(self):
        """Set up the test instance."""

    def test_properties(self):
        """FileSequence: Test getting/setting simple properties."""
        fseq = FileSequence()
        self.assertIsNone(fseq.ext)
        self.assertIsNone(fseq.name)
        self.assertIsNone(fseq.path)

        fseq.name = self._test_name
        self.assertEqual(fseq.name, self._test_name)
        self.assertIsNone(fseq.path)

        fseq = FileSequence()
        fseq.path = self._test_path
        self.assertIsNone(fseq.name)
        self.assertEqual(fseq.path, self._test_path)

        fseq = FileSequence()
        fseq.ext = self._test_ext
        fseq.name = self._test_name
        fseq.path = self._test_path
        self.assertEqual(fseq.ext, self._test_ext)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.path, self._test_path)

        fseq.path = self._test_path + os.sep
        self.assertEqual(fseq.path, self._test_path)

        fseq = FileSequence()
        fseq.name = os.path.join(self._test_path, self._test_name)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.path, self._test_path)

    def test_simple_containment(self):
        """FileSequence: Test if frames are contained by a sequence."""
        chunk1 = FrameChunk(first=1, last=11, step=1, pad=1)
        frames1 = [str(x) for x in xrange(1, 12)]
        chunk2 = FrameChunk(first=1, last=11, step=1, pad=4)
        frames2 = ["%04d" % x for x in xrange(1, 12)]
        chunk3 = FrameChunk(first=91, last=102, step=2, pad=4)
        frames3 = ["%04d" % x for x in xrange(91, 103, 2)]

        file_path = os.path.join(self._test_path, self._test_name)
        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=frames1, pad=1)

        self.assertIn(1, fseq)
        self.assertIn("1", fseq)
        self.assertNotIn("0001", fseq)
