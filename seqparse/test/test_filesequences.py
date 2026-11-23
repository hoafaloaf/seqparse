"""Test the FrameSequence class."""

import os
import unittest
from unittest import mock

from seqparse import sequences, test

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
        chunk = sequences.FrameChunk(first=1, last=11, step=2, pad=4)
        file_name = f"{file_path}.{chunk}.{self._test_ext}"

        file_names = set()
        for frame in chunk:
            file_names.add(f"{file_path}.{frame}.{self._test_ext}")

        fseq = sequences.FileSequence(file_name)
        self.assertEqual(fseq.path, self._test_root)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.pad, 4)
        self.assertEqual(set(fseq), file_names)

    def test_properties(self):
        """FileSequence: Test getting/setting simple properties."""
        fseq = sequences.FileSequence()
        self.assertIsNone(fseq.ext)
        self.assertIsNone(fseq.name)
        self.assertIsNone(fseq.path)

        fseq.name = self._test_name
        self.assertEqual(fseq.name, self._test_name)
        self.assertIsNone(fseq.path)

        fseq = sequences.FileSequence()
        fseq.path = self._test_root
        self.assertIsNone(fseq.name)
        self.assertEqual(fseq.path, self._test_root)

        fseq = sequences.FileSequence()
        fseq.ext = self._test_ext
        fseq.name = self._test_name
        fseq.path = self._test_root
        self.assertEqual(fseq.ext, self._test_ext)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.path, self._test_root)

        fseq.path = self._test_root + os.sep
        self.assertEqual(fseq.path, self._test_root)

        fseq = sequences.FileSequence()
        fseq.name = os.path.join(self._test_root, self._test_name)
        self.assertEqual(fseq.name, self._test_name)
        self.assertEqual(fseq.path, self._test_root)

    def test_output(self):
        """FileSequence: Test string output."""
        file_path = os.path.join(self._test_root, self._test_name)

        chunk = sequences.FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk
        )

        file_name = f"{file_path}.{chunk}.{self._test_ext}"

        self.assertEqual(file_name, str(fseq))

        fseq = sequences.FileSequence(frames=chunk)
        with self.assertRaises(ValueError):
            str(fseq)

    def test_frame_containment(self):
        """FileSequence: Test if frames are contained by a sequence."""
        file_path = os.path.join(self._test_root, self._test_name)

        chunk1 = sequences.FrameChunk(first=1, last=11, step=1, pad=1)
        seq1 = sequences.FrameSequence(chunk1)
        frames1 = [str(x) for x in range(1, 12)]

        for frames in (frames1, chunk1, seq1):
            fseq = sequences.FileSequence(
                name=file_path, ext=self._test_ext, frames=frames, pad=1
            )

            for frame in frames:
                file_name = f"{file_path}.{frame}.{self._test_ext}"
                self.assertIn(frame, fseq)
                self.assertIn(int(frame), fseq)
                self.assertIn(file_name, fseq)
                self.assertNotIn(f"{int(frame):04d}", fseq)

        chunk2 = sequences.FrameChunk(first=1, last=11, step=1, pad=4)
        seq2 = sequences.FrameSequence(chunk2)
        frames2 = [f"{x:04d}" for x in range(1, 12)]

        for frames in (frames2, chunk2, seq2):
            fseq = sequences.FileSequence(
                name=file_path, ext=self._test_ext, frames=frames, pad=4
            )

            for frame in frames:
                file_name = f"{file_path}.{frame}.{self._test_ext}"
                self.assertIn(frame, fseq)
                self.assertIn(int(frame), fseq)
                self.assertIn(file_name, fseq)
                self.assertNotIn(str(int(frame)), fseq)

    def test_file_containment(self):
        """FileSequence: Test if files are contained by a sequence."""
        file_path = os.path.join(self._test_root, self._test_name)
        frames = list(range(1, 12))

        seq1 = sequences.FrameSequence(frames, pad=1)
        fseq1 = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=seq1
        )
        file_names1 = [f"{file_path}.{x}.{self._test_ext}" for x in frames]

        for file_name in file_names1:
            self.assertIn(file_name, fseq1)

        bad_file_names1 = [f"{file_path}.{x}.{self._test_ext}" for x in (0, 12)]

        for file_name in bad_file_names1:
            self.assertNotIn(file_name, fseq1)

        seq2 = sequences.FrameSequence(frames, pad=4)
        fseq2 = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=seq2
        )
        file_names2 = [f"{file_path}.{x:04d}.{self._test_ext}" for x in frames]

        for file_name in file_names2:
            self.assertIn(file_name, fseq2)

        bad_file_names2 = [
            f"{file_path}.{x:04d}.{self._test_ext}" for x in (0, 12)
        ]

        for file_name in bad_file_names2:
            self.assertNotIn(file_name, fseq2)

    def test_iteration(self):
        """FileSequence: Test iteration over an instance."""
        file_path = os.path.join(self._test_root, self._test_name)

        data = [
            (list(range(1, 6)), 4),
            (list(range(1, 21, 2)) + list(range(100, 105)), 1),
        ]

        for frames, pad in data:
            fseq = sequences.FileSequence(
                name=file_path, ext=self._test_ext, frames=frames, pad=pad
            )
            file_names = []
            for frame in frames:
                file_names.append(
                    f"{file_path}.{frame:0{pad}d}.{self._test_ext}"
                )

            self.assertEqual(set(file_names), set(fseq))

            print("\n\n  INPUT FILES\n  -----------")
            print("\n".join(f"  {x}" for x in file_names))
            print("\n  ITERATION\n  ---------")
            print("  o forward: ")
            print("\n".join(f"    - {x}" for x in fseq))
            print("  o backward:")
            print("\n".join(f"    - {x}" for x in reversed(fseq)))

    def test_inversion(self):
        """FileSequence: Test frame inversion (ie, report missing frames)."""
        file_path = os.path.join(self._test_root, self._test_name)

        chunk_in = sequences.FrameChunk(first=1, last=11, step=2, pad=4)
        fseq = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in
        )
        expected = f"{file_path}.0002-0010x2.{self._test_ext}"
        inverted = fseq.invert()

        print("\n\n  SEQUENCE\n  --------")
        print("  input files:   ", fseq)
        print("  expected files:", expected)
        print("  returned files:", inverted)

        self.assertEqual(str(inverted), expected)

        chunk1 = sequences.FrameChunk(first=1, last=9, step=2, pad=4)
        chunk2 = sequences.FrameChunk(first=10, last=20, step=5, pad=4)
        seq_in = sequences.FrameSequence(chunk1)
        seq_in.add(chunk2)
        seq_in.add("0021")
        fseq = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=seq_in
        )

        # Frames 1-9x2, 10-20x5 and 21 are present, so these are missing.
        expected = (
            f"{file_path}.0002-0008x2,0011-0014,0016-0019.{self._test_ext}"
        )
        inverted = fseq.invert()

        print("\n  COMPLEX FRAME\n  ------------")
        print("  input frames:   ", fseq)
        print("  expected frames:", expected)
        print("  returned frames:", inverted)
        print("")

        self.assertEqual(str(inverted), expected)

        chunk_in = sequences.FrameChunk(first=1, last=10, pad=2)
        fseq = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=chunk_in
        )
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
        fseq0 = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=list(range(1, 11)), pad=4
        )
        fseq1 = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames=list(range(1, 11)), pad=4
        )
        fseq2 = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames="0001-0010"
        )
        fseq3 = sequences.FileSequence(
            name=file_path, ext=self._test_ext, frames="001-010"
        )
        fseq4 = sequences.FileSequence(
            name=self._test_name, ext=self._test_ext, frames="0001-0010"
        )

        seq0 = sequences.FrameSequence(list(range(1, 11)), pad=4)

        self.assertEqual(fseq0, fseq1)
        self.assertEqual(fseq0, fseq2)
        self.assertNotEqual(fseq0, fseq3)
        self.assertNotEqual(fseq0, fseq4)
        self.assertNotEqual(fseq0, seq0)

    @mock.patch("seqparse.sequences.os.stat")
    def test_stat_queries(self, mock_api_call):
        """File: Test stat setting and queries."""
        mock_api_call.side_effect = test.mock_os_stat

        file_name = "test.0001.py"
        full_name = os.path.join(self._test_root, file_name)

        fseq = sequences.FileSequence(full_name)

        self.assertEqual(fseq.stat(), {})
        self.assertIsNone(fseq.stat(1))
        self.assertIsNone(fseq.stat("0001"))

        with self.assertRaises(ValueError):
            fseq.stat(lazy=True)

        with self.assertRaises(ValueError):
            fseq.stat(force=True)

        stat = fseq.stat(1, lazy=True)
        self.assertEqual(stat.st_size, 7975)
        self.assertEqual(stat.st_mtime, 1490908305)
        self.assertEqual(fseq.size, 7975)
        self.assertEqual(fseq.mtime, 1490908305)

        fseq = sequences.FileSequence(full_name)
        stat = fseq.stat(1, force=True)
        self.assertEqual(fseq.stat(1).st_size, 7975)
        self.assertEqual(fseq.stat(1).st_mtime, 1490908305)
        self.assertEqual(fseq.size, 7975)
        self.assertEqual(fseq.mtime, 1490908305)

    def test_cloning(self):
        """FileSequence: Test cloning from an existing instance."""
        file_name = "test.0001-0005,0010.py"
        full_name = os.path.join(self._test_root, file_name)

        parent = sequences.FileSequence(full_name)
        clone = sequences.FileSequence(parent)

        self.assertEqual(str(parent), str(clone))
        for attr in ("full_name", "name", "pad", "path"):
            self.assertEqual(getattr(parent, attr), getattr(clone, attr))

    def test_frame_properties(self):
        """FileSequence: Test frames, pretty_frames properties."""
        frames = sequences.FrameSequence(list(range(1, 6)), pad=4)
        full_name = os.path.join(self._test_root, self._test_name)
        fseq = sequences.FileSequence(name=full_name, frames=frames, ext="exr")

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

        input_seq1 = sequences.FileSequence(
            ext="py", frames=frames1, name=full_name1, pad=4
        )
        input_seq2 = sequences.FileSequence(
            ext="py", frames=frames2, name=full_name1, pad=4
        )
        input_seq3 = sequences.FileSequence(
            ext="py", frames=frames2, name=full_name3, pad=4
        )

        # Caching disk stats (because mocking os.stat is hard):
        for seq in (input_seq1, input_seq2):
            for file_name in seq:
                frame = seq.file_name_match(file_name, as_dict=True)["frame"]
                assert frame is not None
                stat = test.mock_os_stat(file_name)
                seq.cache_stat(frame, stat)

        # Invalid base name ...
        with self.assertRaises(ValueError):
            input_seq1.update(input_seq3)

        # Valid base name, testing stat copies as well.
        input_seq1.update(input_seq2)
        self.assertEqual(str(input_seq1), f"{full_name1}.0001-0004,0006.py")
        self.assertEqual(sorted(input_seq1.stat()), [1, 2, 3, 4, 6])

    def test_discard(self):
        """FileSequence: Test the discard method."""
        full_name = os.path.join(self._test_root, self._test_name)
        frames = list(range(1, 6))

        input_seq = sequences.FileSequence(
            ext=self._test_ext, frames=frames, name=full_name
        )

        self.assertIn(frames[0], input_seq)
        input_seq.discard(frames[0])
        self.assertNotIn(frames[0], input_seq)


###############################################################################
# class: TestEmptyFiles


def _stat_of_size(size, mtime=1):
    """A stat_result for a regular file of the given size."""
    return os.stat_result((0o100644, 1, 2, 1, 0, 0, size, 1, mtime, 1))


class TestEmptyFiles(unittest.TestCase):
    """FileSequence.empty_files() finds the zero-byte files."""

    def make(self, sizes, **kwargs):
        """A FileSequence whose frames have the given cached sizes."""
        seq = sequences.FileSequence(
            name=os.path.join("renders", "plate"),
            ext="exr",
            frames=list(sizes),
            pad=4,
            **kwargs,
        )
        for frame, size in sizes.items():
            seq.cache_stat(frame, _stat_of_size(size, mtime=frame))
        return seq

    def test_finds_only_the_zero_byte_frames(self):
        """Frames 3 and 5 are empty; the rest are not."""
        empty = self.make({1: 10, 2: 10, 3: 0, 4: 10, 5: 0}).empty_files()
        self.assertEqual(
            str(empty), os.path.join("renders", "plate.0003,0005.exr")
        )
        self.assertEqual((empty.ext, empty.pad), ("exr", 4))
        self.assertEqual((empty.name, empty.path), ("plate", "renders"))

    def test_keeps_the_cached_stats(self):
        """The result carries the stats of the files it reports."""
        empty = self.make({1: 10, 3: 0, 5: 0}).empty_files()
        self.assertEqual(empty.size, 0)
        self.assertEqual(empty.mtime, 5)

    def test_nothing_empty_is_falsy(self):
        """A sequence without empty files gives an empty (falsy) result."""
        self.assertFalse(self.make({1: 10, 2: 1}).empty_files())

    def test_frames_without_stats_are_never_reported(self):
        """Not statted is not the same as empty."""
        seq = sequences.FileSequence(name="plate", ext="exr", frames=[1, 2])
        self.assertFalse(seq.empty_files())

    def test_original_is_unchanged(self):
        """The sequence itself keeps all its frames and stats."""
        seq = self.make({1: 10, 2: 0})
        seq.empty_files()
        self.assertEqual(
            str(seq), os.path.join("renders", "plate.0001,0002.exr")
        )
        self.assertEqual(sorted(seq.stat()), [1, 2])


class TestStandardSetMethods(unittest.TestCase):
    """Iterating a FileSequence gives file names, so those must work back."""

    def make(self):
        """A three-frame sequence with cached stats."""
        seq = sequences.FileSequence(
            name=os.path.join("shots", "plate"),
            ext="exr",
            frames=[1, 2, 3],
            pad=4,
        )
        for number in (1, 2, 3):
            seq.cache_stat(number, _stat_of_size(number))
        return seq

    def test_discard_and_remove_accept_file_names(self):
        """A member's file name removes the frame (and its stats)."""
        seq = self.make()
        name = os.path.join("shots", "plate.0002.exr")
        seq.discard(name)
        self.assertEqual(list(seq.frames), ["0001", "0003"])
        self.assertEqual(sorted(seq.stat()), [1, 3])
        seq.remove(os.path.join("shots", "plate.0001.exr"))
        self.assertEqual(list(seq.frames), ["0003"])

    def test_discarding_a_file_that_is_not_a_member_does_nothing(self):
        """Per standard set semantics."""
        seq = self.make()
        seq.discard(os.path.join("shots", "plate.0009.exr"))
        self.assertEqual(list(seq.frames), ["0001", "0002", "0003"])

    def test_garbage_is_still_an_error(self):
        """Only file names were added to what discard understands."""
        for garbage in (
            "not a frame",
            os.path.join("elsewhere", "plate.0001.exr"),  # not one of ours
        ):
            with self.subTest(value=garbage), self.assertRaises(ValueError):
                self.make().discard(garbage)

    def test_pop_clear_and_in_place_difference_work(self):
        """The inherited methods feed iterated names back into discard."""
        seq = self.make()
        self.assertEqual(seq.pop(), os.path.join("shots", "plate.0001.exr"))
        other = sequences.FileSequence(
            name=os.path.join("shots", "plate"), ext="exr", frames=[2], pad=4
        )
        seq -= other
        self.assertEqual(list(seq.frames), ["0003"])
        seq.clear()
        self.assertEqual((len(seq), seq.stat()), (0, {}))

    def test_empty_files_ignores_frames_that_are_not_members(self):
        """Stats cached for a frame the sequence does not have."""
        seq = sequences.FileSequence(name="plate", ext="exr", frames=[], pad=4)
        seq.cache_stat(5, _stat_of_size(0))
        self.assertFalse(seq.empty_files())
