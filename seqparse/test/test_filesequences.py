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

    def test_containment(self):
        """FileSequence: Test if frames are contained by a sequence."""
        file_path = os.path.join(self._test_path, self._test_name)

        chunk1 = FrameChunk(first=1, last=11, step=1, pad=1)
        seq1 = FrameSequence(chunk1)
        frames1 = [str(x) for x in xrange(1, 12)]
        chunk2 = FrameChunk(first=1, last=11, step=1, pad=4)
        seq2 = FrameSequence(chunk2)
        frames2 = ["%04d" % x for x in xrange(1, 12)]

        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=frames1, pad=1)

        for frame in chunk1:
            self.assertIn(frame, fseq)
            self.assertIn(int(frame), fseq)
            self.assertNotIn("%04d" % int(frame), fseq)

        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=chunk1)

        for frame in chunk1:
            self.assertIn(frame, fseq)
            self.assertIn(int(frame), fseq)
            self.assertNotIn("%04d" % int(frame), fseq)

        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=seq1)

        for frame in seq1:
            self.assertIn(frame, fseq)
            self.assertIn(int(frame), fseq)
            self.assertNotIn("%04d" % int(frame), fseq)

        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=frames2, pad=4)

        for frame in chunk2:
            self.assertIn(frame, fseq)
            self.assertIn(int(frame), fseq)
            self.assertNotIn(str(int(frame)), fseq)

        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=chunk2)

        for frame in chunk2:
            self.assertIn(frame, fseq)
            self.assertIn(int(frame), fseq)
            self.assertNotIn(str(int(frame)), fseq)

        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=seq2)

        for frame in seq2:
            self.assertIn(frame, fseq)
            self.assertIn(int(frame), fseq)
            self.assertNotIn(str(int(frame)), fseq)

    def test_iteration(self):
        """FrameSequence: Test iteration over an instance."""
        file_path = os.path.join(self._test_path, self._test_name)

        data = [(range(1, 6), 4), (range(1, 21, 2) + range(100, 105), 1)]

        for frames, pad in data:
            fseq = FileSequence(
                name=file_path, ext=self._test_ext, frames=frames, pad=pad)
            file_names = list()
            for frame in frames:
                file_name = "%s.%0*d.%s" % (file_path, pad, frame,
                                            self._test_ext)
                file_names.append(file_name)

            self.assertEqual(set(file_names), set(fseq))

            print "\n\n  INPUT FILES\n  -----------"
            print "\n".join("  %s" % x for x in file_names)
            print "\n  ITERATION\n  ---------"
            print "  o forward: "
            print "\n".join("    - %s" % x for x in fseq)
            print "  o backward:"
            print "\n".join(list("    - %s" % x for x in reversed(fseq)))
