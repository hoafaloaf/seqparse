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

    def test_output(self):
        """FileSequence: Test string output."""
        file_path = os.path.join(self._test_path, self._test_name)

        chunk = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=chunk)

        file_name = "%s.%s.%s" % (file_path, chunk, self._test_ext)

        self.assertEqual(file_name, str(fseq))

    def test_frame_containment(self):
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

    def test_file_containment(self):
        """FileSequence: Test if files are contained by a sequence."""
        file_path = os.path.join(self._test_path, self._test_name)
        frames = range(1, 12)

        # TODO: See why this doesn't work: seq1 = FileSequence(frames, pad=1)
        seq1 = FrameSequence(frames, pad=1)
        fseq1 = FileSequence(name=file_path, ext=self._test_ext, frames=seq1)
        file_names1 = [
            "%s.%s.%s" % (file_path, x, self._test_ext) for x in frames
        ]

        for file_name in file_names1:
            self.assertIn(file_name, fseq1)

        bad_file_names1 = [
            "%s.%s.%s" % (file_path, x, self._test_ext) for x in (0, 12)
        ]

        for file_name in bad_file_names1:
            self.assertNotIn(file_name, fseq1)

        seq2 = FrameSequence(frames, pad=4)
        fseq2 = FileSequence(name=file_path, ext=self._test_ext, frames=seq2)
        file_names2 = [
            "%s.%04d.%s" % (file_path, x, self._test_ext) for x in frames
        ]

        for file_name in file_names2:
            self.assertIn(file_name, fseq2)

        bad_file_names2 = [
            "%s.%0d.%s" % (file_path, x, self._test_ext) for x in (0, 12)
        ]

        for file_name in bad_file_names2:
            self.assertNotIn(file_name, fseq2)

    def test_iteration(self):
        """FileSequence: Test iteration over an instance."""
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

    def test_inversion(self):
        """FileSequence: Test frame inversion (ie, report missing frames)."""
        file_path = os.path.join(self._test_path, self._test_name)

        chunk_in = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in)
        chunk_out = FrameChunk(first=2, last=10, step=2, pad=4)
        expected = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_out)
        inverted = fseq.invert()

        print "\n\n  SEQUENCE\n  --------"
        print "  input files:   ", fseq
        print "  expected files:", expected
        print "  returned files:", inverted

        self.assertEqual(str(inverted), str(expected))

        chunk1 = FrameChunk(first=1, last=9, step=2, pad=4)
        chunk2 = FrameChunk(first=10, last=20, step=5, pad=4)
        seq_in = FrameSequence(chunk1)
        seq_in.add(chunk2)
        seq_in.add("0021")
        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=seq_in)

        seq_out = FrameSequence(pad=4)
        seq_out.add(chunk1.invert())
        seq_out.add(chunk2.invert())
        seq_out.invert()
        expected = FileSequence(
            name=file_path, ext=self._test_ext, frames=seq_in.invert())
        inverted = fseq.invert()

        print "\n  COMPLEX FRAME\n  ------------"
        print "  input frames:   ", fseq
        print "  expected frames:", expected
        print "  returned frames:", inverted
        print

        self.assertEqual(str(inverted), str(expected))

        chunk_in = FrameChunk(first=1, last=10, pad=2)
        fseq = FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in)
        expected = ""
        inverted = fseq.invert()

        print "\n\n  SEQUENCE\n  --------"
        print "  input files:   ", fseq
        print "  expected files:", expected
        print "  returned files:", inverted

        self.assertEqual(str(inverted), str(expected))
