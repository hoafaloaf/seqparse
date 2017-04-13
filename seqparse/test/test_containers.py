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
    """Test the container classes used by the Seqparse module."""

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
