"""Test the container classes used by the Seqparse module."""

# "Future" Libraries
from __future__ import print_function

# Standard Libraries
import os
import unittest

# Third Party Libraries
import mock
from builtins import range
from future.utils import lrange

from . import (DirEntry, generate_entries, initialise_mock_scandir_data,
               mock_scandir_deep)
from .. import (__version__, get_parser, get_sequence, get_version, invert,
                validate_frame_sequence)
from ..containers import FileExtension
from ..sequences import FileSequence, FrameChunk, FrameSequence


###############################################################################
# class: TestFileSequenceContainer


class TestFileSequenceContainer(unittest.TestCase):
    """Test the FileSequenceContainer class used by the Seqparse module."""

    _test_ext = "exr"
    _test_file_name1 = "kitty"
    _test_file_name2 = "cat"
    _test_root = "/pretty/kitty".replace("/", os.sep)
    _singletons = ["singleton0.jpg", "singleton1.jpg"]

    def setUp(self):
        """Set up the test case."""
        frames1 = lrange(0, 5)
        frames2 = lrange(1, 6)

        full_name1 = os.path.join(self._test_root, self._test_file_name1)
        full_name2 = os.path.join(self._test_root, self._test_file_name2)

        # yapf: disable
        self._input_seqs = [
            FileSequence(
                ext=self._test_ext, frames=frames1, name=full_name1, pad=4),
            FileSequence(
                ext=self._test_ext, frames=frames2, name=full_name1, pad=4),
            FileSequence(
                ext=self._test_ext, frames=frames1, name=full_name2, pad=4),
            FileSequence(
                ext=self._test_ext, frames=frames2, name=full_name2, pad=4)
        ]
        # yapf: enable

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_equality(self, fake_isfile):
        """FileSequenceContainer: Test equality."""
        fake_isfile.return_value = True

        containers = list()
        for input_seq in self._input_seqs:
            parser = get_parser()

            # Add in the source FileSequence files one-by-one.
            parser.scan_path(list(map(str, input_seq)))
            containers.append(parser.sequences[input_seq.path][input_seq.name])

        self.assertEqual(containers[0], containers[1])
        self.assertEqual(containers[2], containers[3])

        self.assertNotEqual(containers[0], containers[2])
        self.assertNotEqual(containers[0], containers[3])
        self.assertNotEqual(containers[1], containers[2])
        self.assertNotEqual(containers[1], containers[3])

        self.assertGreater(containers[0], containers[2])
        self.assertGreater(containers[1], containers[3])

        for container in containers:
            fseq = "\n".join(str(x) for x in container.output())
            self.assertNotEqual(fseq, container)
            self.assertGreater(fseq, container)

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_membership(self, fake_isfile):
        """FileSequenceContainer: Test membership setting, deletion."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq = self._input_seqs[0]
        parser.scan_path(list(map(str, input_seq)))
        container = parser.sequences[input_seq.path][input_seq.name]

        for value in ([], FileExtension(name="tif")):
            with self.assertRaises(ValueError):
                container["tiff"] = value

        # Test __setitem__
        raised = False
        file_ext = FileExtension(name="tiff")
        try:
            container["tiff"] = file_ext
        except ValueError:
            raised = False
        self.assertFalse(
            raised, "Unable to set specified value: {!r}".format(file_ext))

        # Test __delitem__
        raised = False
        ext = "tiff"
        try:
            del container["tiff"]
        except ValueError:
            raised = False
        self.assertFalse(raised,
                         "Unable to delete specified value: {!r}".format(ext))

        with self.assertRaises(KeyError):
            del container["tiff"]

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_properties(self, fake_isfile):
        """FileSequenceContainer: Test class properties."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq = self._input_seqs[0]
        parser.scan_path(list(map(str, input_seq)))
        container = parser.sequences[input_seq.path][input_seq.name]

        self.assertEqual(container.path, input_seq.path)
        self.assertEqual(container.name, input_seq.name)


###############################################################################
# Class: TestFileExtension


class TestFileExtension(unittest.TestCase):
    """Test the FileExtension class used by the Seqparse module."""

    _test_ext = "exr"
    _test_file_name1 = "kitty"
    _test_file_name2 = "cat"
    _test_root = "/pretty/kitty".replace("/", os.sep)
    _singletons = ["singleton0.jpg", "singleton1.jpg"]

    def setUp(self):
        """Set up the test case."""
        frames1 = lrange(0, 5)
        frames2 = lrange(1, 6)

        full_name1 = os.path.join(self._test_root, self._test_file_name1)
        full_name2 = os.path.join(self._test_root, self._test_file_name2)

        # yapf: disable
        self._input_seqs = [
            FileSequence(
                ext=self._test_ext, frames=frames1, name=full_name1, pad=4),
            FileSequence(
                ext=self._test_ext, frames=frames2, name=full_name1, pad=4),
            FileSequence(
                ext=self._test_ext, frames=frames1, name=full_name2, pad=4),
            FileSequence(
                ext=self._test_ext, frames=frames2, name=full_name2, pad=4)
        ]
        # yapf: enable

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_properties(self, fake_isfile):
        """FileExtension: Test class properties."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq = self._input_seqs[0]
        parser.scan_path(list(map(str, input_seq)))
        container = parser.sequences[input_seq.path][input_seq.name]

        file_ext = container[self._test_ext]
        self.assertEqual(input_seq.ext, file_ext.name)

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_membership(self, fake_isfile):
        """FileExtension: Test membership setting, deletion."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq1 = self._input_seqs[0]
        input_seq2 = FileSequence(input_seq1)
        input_seq2.pad = 2
        input_seq3 = FileSequence(input_seq1)
        input_seq3.pad = 3

        parser.scan_path(list(map(str, input_seq1)))
        container = parser.sequences[input_seq1.path][input_seq1.name]

        file_ext = container[self._test_ext]

        # Test __setitem__
        raised = False
        try:
            file_ext[2] = input_seq2
        except ValueError:
            raised = False
        self.assertFalse(
            raised, "Unable to set specified value: {!r}".format(input_seq2))

        with self.assertRaises(ValueError):
            file_ext[2] = str(input_seq2)

        raised = False
        try:
            file_ext[3] = lrange(0, 5)
        except ValueError:
            raised = False
        self.assertFalse(
            raised, "Unable to set specified value: {!r}".format(input_seq2))

        self.assertEqual(str(file_ext[3]), str(input_seq3))

        # Test __delitem__
        raised = False
        pad = 3
        try:
            del file_ext[pad]
        except ValueError:
            raised = False
        self.assertFalse(raised,
                         "Unable to delete specified value: {!r}".format(pad))

        with self.assertRaises(KeyError):
            del file_ext[pad]

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_membership(self, fake_isfile):
        """FileExtension: Test membership setting, deletion."""
        fake_isfile.return_value = True
        frames1 = [1, 2, 3, 10, 11, 12, 100, 101, 102]
        full_name = os.path.join(self._test_root, self._test_file_name1)

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq1 = FileSequence(
            ext=self._test_ext, frames=frames1, name=full_name)
        parser.scan_path(list(map(str, input_seq1)))
        container = parser.sequences[input_seq1.path][input_seq1.name]

        file_ext = container[self._test_ext]

        # Test __setitem__, __delitem__ ...
        frames4 = lrange(1000, 1003)
        input_seq4 = FileSequence(
            ext=self._test_ext, frames=frames4, name=full_name)

        for test_input in (frames4, input_seq4):
            raised = False
            blurb = ""
            try:
                file_ext[4] = test_input
                del file_ext[4]
            except KeyError:
                raised = False
                blurb = "Unable to delete specified value: {!r}"
            except ValueError:
                raised = False
                blurb = "Unable to set specified value: {!r}"

            self.assertFalse(raised, blurb.format(test_input))

        with self.assertRaises(KeyError):
            del file_ext[4]

        with self.assertRaises(ValueError):
            file_ext[4] = str(input_seq4)

    @mock.patch("seqparse.seqparse.os.path.isfile")
    def test_output(self, fake_isfile):
        """FileExtension: Verify sequence output."""
        fake_isfile.return_value = True
        frames1 = [1, 2, 3, 10, 11, 12, 100, 101, 102]
        full_name = os.path.join(self._test_root, self._test_file_name1)

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq1 = FileSequence(
            ext=self._test_ext, frames=frames1, name=full_name)
        parser.scan_path(list(map(str, input_seq1)))
        container = parser.sequences[input_seq1.path][input_seq1.name]

        file_ext = container[self._test_ext]
        output = "\n".join(map(str, file_ext.output()))

        self.assertEqual(output, str(input_seq1))
