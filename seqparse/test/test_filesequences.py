"""Test the FrameSequence class."""

import os
import unittest
from unittest import mock

from . import mock_os_stat
from ..sequences import FileSequence, FrameChunk, FrameSequence

###############################################################################
# class: TestFileSequences


class TestFileSequences(unittest.TestCase):
    """Test basic functionality on the FileSequence class."""

    _test_ext = "exr"
    _test_name = "cat"
    _test_root = "/pretty/kitty".replace("/", os.sep)

    def setUp(self):
        """Set up the test instance."""

    def test_file_name_initialization(self):
        """FileSequence: Test initialization of an instance by file name."""
        file_path = os.path.join(self._test_root, self._test_name)
        chunk = FrameChunk(first=1, last=11, step=2, pad=4)
        file_name = f'{file_path}.{chunk}.{self._test_ext}'

        file_names = set()
        for frame in chunk:
            file_names.add(f'{file_path}.{frame}.{self._test_ext}')

        fseq = FileSequence(file_name)
        self.assertEqual(fseq.path, self._test_root)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.pad, 4)
        self.assertEqual(set(fseq), file_names)

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
        fseq.path = self._test_root
        self.assertIsNone(fseq.name)
        self.assertEqual(fseq.path, self._test_root)

        fseq = FileSequence()
        fseq.ext = self._test_ext
        fseq.name = self._test_name
        fseq.path = self._test_root
        self.assertEqual(fseq.ext, self._test_ext)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.path, self._test_root)

        fseq.path = self._test_root + os.sep
        self.assertEqual(fseq.path, self._test_root)

        fseq = FileSequence()
        fseq.name = os.path.join(self._test_root, self._test_name)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.path, self._test_root)

    def test_output(self):
        """FileSequence: Test string output."""
        file_path = os.path.join(self._test_root, self._test_name)

        chunk = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(name=file_path, ext=self._test_ext, frames=chunk)

        file_name = f'{file_path}.{chunk}.{self._test_ext}'

        self.assertEqual(file_name, str(fseq))

        fseq = FileSequence(frames=chunk)
        with self.assertRaises(AttributeError):
            str(fseq)

    def test_frame_containment(self):
        """FileSequence: Test if frames are contained by a sequence."""
        file_path = os.path.join(self._test_root, self._test_name)

        chunk1 = FrameChunk(first=1, last=11, step=1, pad=1)
        seq1 = FrameSequence(chunk1)
        frames1 = [str(x) for x in range(1, 12)]

        for frames in (frames1, chunk1, seq1):
            fseq = FileSequence(name=file_path,
                                ext=self._test_ext,
                                frames=frames,
                                pad=1)

            for frame in frames:
                file_name = f'{file_path}.{frame}.{self._test_ext}'
                self.assertIn(frame, fseq)
                self.assertIn(int(frame), fseq)
                self.assertIn(file_name, fseq)
                self.assertNotIn(f'{int(frame):04d}', fseq)

        chunk2 = FrameChunk(first=1, last=11, step=1, pad=4)
        seq2 = FrameSequence(chunk2)
        frames2 = [f'{x:04d}' for x in range(1, 12)]

        for frames in (frames2, chunk2, seq2):
            fseq = FileSequence(name=file_path,
                                ext=self._test_ext,
                                frames=frames,
                                pad=4)

            for frame in frames:
                file_name = f'{file_path}.{frame}.{self._test_ext}'
                self.assertIn(frame, fseq)
                self.assertIn(int(frame), fseq)
                self.assertIn(file_name, fseq)
                self.assertNotIn(str(int(frame)), fseq)

    def test_file_containment(self):
        """FileSequence: Test if files are contained by a sequence."""
        file_path = os.path.join(self._test_root, self._test_name)
        frames = list(range(1, 12))

        seq1 = FrameSequence(frames, pad=1)
        fseq1 = FileSequence(name=file_path, ext=self._test_ext, frames=seq1)
        file_names1 = [f'{file_path}.{x}.{self._test_ext}' for x in frames]

        for file_name in file_names1:
            self.assertIn(file_name, fseq1)

        bad_file_names1 = [
            f'{file_path}.{x}.{self._test_ext}' for x in (0, 12)
        ]

        for file_name in bad_file_names1:
            self.assertNotIn(file_name, fseq1)

        seq2 = FrameSequence(frames, pad=4)
        fseq2 = FileSequence(name=file_path, ext=self._test_ext, frames=seq2)
        file_names2 = [f'{file_path}.{x:04d}.{self._test_ext}' for x in frames]

        for file_name in file_names2:
            self.assertIn(file_name, fseq2)

        bad_file_names2 = [
            f'{file_path}.{x:04d}.{self._test_ext}' for x in (0, 12)
        ]

        for file_name in bad_file_names2:
            self.assertNotIn(file_name, fseq2)

    def test_iteration(self):
        """FileSequence: Test iteration over an instance."""
        file_path = os.path.join(self._test_root, self._test_name)

        data = [(list(range(1, 6)), 4),
                (list(range(1, 21, 2)) + list(range(100, 105)), 1)]

        for frames, pad in data:
            fseq = FileSequence(name=file_path,
                                ext=self._test_ext,
                                frames=frames,
                                pad=pad)
            file_names = []
            for frame in frames:
                file_names.append(
                    f'{file_path}.{frame:0{pad}d}.{self._test_ext}')

            self.assertEqual(set(file_names), set(fseq))

            print("\n\n  INPUT FILES\n  -----------")
            print("\n".join(f'  {x}' for x in file_names))
            print("\n  ITERATION\n  ---------")
            print("  o forward: ")
            print("\n".join(f'    - {x}' for x in fseq))
            print("  o backward:")
            print("\n".join(f'    - {x}' for x in reversed(fseq)))

    def test_inversion(self):
        """FileSequence: Test frame inversion (ie, report missing frames)."""
        file_path = os.path.join(self._test_root, self._test_name)

        chunk_in = FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = FileSequence(name=file_path,
                            ext=self._test_ext,
                            frames=chunk_in)
        chunk_out = FrameChunk(first=2, last=10, step=2, pad=4)
        expected = FileSequence(name=file_path,
                                ext=self._test_ext,
                                frames=chunk_out)
        inverted = fseq.invert()

        print("\n\n  SEQUENCE\n  --------")
        print("  input files:   ", fseq)
        print("  expected files:", expected)
        print("  returned files:", inverted)

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
        expected = FileSequence(name=file_path,
                                ext=self._test_ext,
                                frames=seq_in.invert())
        inverted = fseq.invert()

        print("\n  COMPLEX FRAME\n  ------------")
        print("  input frames:   ", fseq)
        print("  expected frames:", expected)
        print("  returned frames:", inverted)
        print("")

        self.assertEqual(str(inverted), str(expected))

        chunk_in = FrameChunk(first=1, last=10, pad=2)
        fseq = FileSequence(name=file_path,
                            ext=self._test_ext,
                            frames=chunk_in)
        expected = ""
        inverted = fseq.invert()

        print("\n  SEQUENCE\n  --------")
        print("  input files:   ", fseq)
        print("  expected files:", expected)
        print("  returned files:", inverted)

        self.assertEqual(str(inverted), str(expected))

    def test_equality(self):
        """FileSequence: Test the equality of instances."""
        file_path = os.path.join(self._test_root, self._test_name)
        fseq0 = FileSequence(name=file_path,
                             ext=self._test_ext,
                             frames=list(range(1, 11)),
                             pad=4)
        fseq1 = FileSequence(name=file_path,
                             ext=self._test_ext,
                             frames=list(range(1, 11)),
                             pad=4)
        fseq2 = FileSequence(name=file_path,
                             ext=self._test_ext,
                             frames="0001-0010")
        fseq3 = FileSequence(name=file_path,
                             ext=self._test_ext,
                             frames="001-010")
        fseq4 = FileSequence(name=self._test_name,
                             ext=self._test_ext,
                             frames="0001-0010")

        seq0 = FrameSequence(list(range(1, 11)), pad=4)

        self.assertEqual(fseq0, fseq1)
        self.assertEqual(fseq0, fseq2)
        self.assertNotEqual(fseq0, fseq3)
        self.assertNotEqual(fseq0, fseq4)
        self.assertNotEqual(fseq0, seq0)

    @mock.patch("seqparse.sequences.os.stat")
    def test_stat_queries(self, mock_api_call):
        """File: Test stat setting and queries."""
        mock_api_call.side_effect = mock_os_stat

        file_name = "test.0001.py"
        full_name = os.path.join(self._test_root, file_name)

        fseq = FileSequence(full_name)

        self.assertEqual(fseq.stat(), {})
        self.assertIsNone(fseq.stat(1))
        self.assertIsNone(fseq.stat("0001"))

        with self.assertRaises(ValueError):
            fseq.stat(lazy=True)

        with self.assertRaises(ValueError):
            fseq.stat(force=True)

        # pylint: disable=E1101
        stat = fseq.stat(1, lazy=True)
        self.assertEqual(stat.st_size, 7975)
        self.assertEqual(stat.st_mtime, 1490908305)
        self.assertEqual(fseq.size, 7975)
        self.assertEqual(fseq.mtime, 1490908305)

        fseq = FileSequence(full_name)
        stat = fseq.stat(1, force=True)
        self.assertEqual(fseq.stat(1).st_size, 7975)
        self.assertEqual(fseq.stat(1).st_mtime, 1490908305)
        self.assertEqual(fseq.size, 7975)
        self.assertEqual(fseq.mtime, 1490908305)
        # pylint: enable=E1101

    def test_cloning(self):
        """FileSequence: Test cloning from an existing instance."""
        file_name = "test.0001-0005,0010.py"
        full_name = os.path.join(self._test_root, file_name)

        parent = FileSequence(full_name)
        clone = FileSequence(parent)

        self.assertEqual(str(parent), str(clone))
        for attr in ("full_name", "name", "pad", "path"):
            self.assertEqual(getattr(parent, attr), getattr(clone, attr))

    def test_frame_properties(self):
        """FileSequence: Test frames, pretty_frames properties."""
        frames = FrameSequence(list(range(1, 6)), pad=4)
        full_name = os.path.join(self._test_root, self._test_name)
        fseq = FileSequence(name=full_name, frames=frames, ext="exr")

        frames_seq = list(frames)
        fseq_frames = list(fseq.frames)

        self.assertEqual(fseq.pretty_frames, str(frames))
        self.assertEqual(frames_seq, fseq_frames)

    def test_update(self):
        """FileSequence: Test the update method."""
        full_name1 = os.path.join(self._test_root, "test")
        full_name3 = os.path.join(self._test_root, "manx")

        frames1 = [1, 2, 3]
        frames2 = [4, 6]

        input_seq1 = FileSequence(ext="py",
                                  frames=frames1,
                                  name=full_name1,
                                  pad=4)
        input_seq2 = FileSequence(ext="py",
                                  frames=frames2,
                                  name=full_name1,
                                  pad=4)
        input_seq3 = FileSequence(ext="py",
                                  frames=frames2,
                                  name=full_name3,
                                  pad=4)

        # Caching disk stats (because mocking os.stat is hard):
        for seq in (input_seq1, input_seq2):
            for file_name in seq:
                frame = seq.file_name_match(file_name, as_dict=True)["frame"]
                stat = mock_os_stat(file_name)
                seq.cache_stat(frame, stat)

        # Invalid base name ...
        with self.assertRaises(ValueError):
            input_seq1.update(input_seq3)

        # Valid base name, testing stat copies as well.
        raised = False
        try:
            input_seq1.update(input_seq2)
        except ValueError:
            raised = True

        blurb = "Unable to update with specified value: {!r}"
        self.assertFalse(raised, blurb.format(input_seq2))

    def test_discard(self):
        """FileSequence: Test the discard method."""
        full_name = os.path.join(self._test_root, self._test_name)
        frames = list(range(1, 6))

        input_seq = FileSequence(ext=self._test_ext,
                                 frames=frames,
                                 name=full_name)

        self.assertIn(frames[0], input_seq)
        input_seq.discard(frames[0])
        self.assertNotIn(frames[0], input_seq)
