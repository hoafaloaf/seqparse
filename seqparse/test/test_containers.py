"""Test the container classes used by the Seqparse module."""

import os
import unittest
from unittest import mock

from . import DirEntry
from .. import get_parser
from ..containers import FileExtension, SingletonContainer
from ..sequences import FileSequence

###############################################################################
# class: TestSingletonContainer


class TestSingletonContainer(unittest.TestCase):
    """Test the SingletonContainer class used by the Seqparse module."""

    _test_root = '/pretty/kitty'.replace('/', os.sep)
    _singletons = ['singleton0.jpg', 'singleton1.jpg']

    def setUp(self):
        """Set up the test case."""

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_properties(self, fake_isfile):
        """SingletonContainer: Test class properties."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source files one-by-one.
        for file_name in self._singletons:
            parser.add_file(os.path.join(self._test_root, file_name))

        container = parser.singletons[self._test_root]
        self.assertEqual(self._test_root, container.path)

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_membership(self, fake_isfile):
        """SingletonContainer: Test class properties."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source files one-by-one.
        for file_name in self._singletons:
            parser.add_file(os.path.join(self._test_root, file_name))

        container = parser.singletons[self._test_root]

        for file_name in self._singletons:
            self.assertIn(file_name, container)

        self.assertEqual(len(container), len(self._singletons))

        container.discard(self._singletons[0])
        self.assertNotIn(self._singletons[0], container)
        self.assertEqual(len(container), len(self._singletons) - 1)

        container.update([self._singletons[0]])
        self.assertEqual(len(container), len(self._singletons))

        file_names = set(container)
        self.assertEqual(file_names, set(self._singletons))

    def test_initialisation(self):
        """SingletonContainer: Test class initialisation."""
        container = SingletonContainer()
        self.assertEqual(len(container), 0)
        self.assertEqual(container.path, '')

        container = SingletonContainer(self._singletons, self._test_root)
        self.assertEqual(len(container), len(self._singletons))
        self.assertEqual(container.path, self._test_root)

    def test_output(self):
        """SingletonContainer: Test output method."""
        file_names = [
            os.path.join(self._test_root, x) for x in sorted(self._singletons)
        ]

        container = SingletonContainer(self._singletons, self._test_root)
        self.assertEqual('\n'.join(file_names), str(container))

        output = [str(x) for x in container.output()]
        self.assertEqual('\n'.join(file_names), str(container))
        self.assertEqual('\n'.join(file_names), '\n'.join(output))

    @mock.patch('seqparse.seqparse.os.scandir')
    def test_stats(self, mock_api_call):
        """SingletonContainer: Test disk stat functionality."""
        input_entries = [DirEntry(os.path.join(self._test_root, 'pony.py'))]

        mock_api_call.return_value = input_entries

        parser = get_parser()
        parser.scan_options['stat'] = True
        parser.scan_path(self._test_root)

        container = parser.singletons[self._test_root]
        self.assertEqual(container.stat('pony.py').st_size, 9436)
        self.assertEqual(container.stat()['pony.py'].st_size, 9436)


###############################################################################
# class: TestFileSequenceContainer


class TestFileSequenceContainer(unittest.TestCase):
    """Test the FileSequenceContainer class used by the Seqparse module."""

    _test_ext = 'exr'
    _test_file_name1 = 'kitty'
    _test_file_name2 = 'cat'
    _test_root = '/pretty/kitty'.replace('/', os.sep)

    def setUp(self):
        """Set up the test case."""
        frames1 = list(range(0, 5))
        frames2 = list(range(1, 6))

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

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_equality(self, fake_isfile):
        """FileSequenceContainer: Test equality."""
        fake_isfile.return_value = True

        containers = []
        for input_seq in self._input_seqs:
            parser = get_parser()

            # Add in the source FileSequence files one-by-one.
            parser.scan_path([str(x) for x in input_seq])
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
            fseq = '\n'.join(str(x) for x in container.output())
            self.assertNotEqual(fseq, container)
            self.assertGreater(fseq, container)

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_membership(self, fake_isfile):
        """FileSequenceContainer: Test membership setting, deletion."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq = self._input_seqs[0]
        parser.scan_path([str(x) for x in input_seq])
        container = parser.sequences[input_seq.path][input_seq.name]

        for value in ([], FileExtension(name='tif')):
            with self.assertRaises(ValueError):
                container['tiff'] = value

        # Test __setitem__
        raised = False
        file_ext = FileExtension(name='tiff')
        try:
            container['tiff'] = file_ext
        except ValueError:
            raised = False
        self.assertFalse(raised,
                         f'Unable to set specified value: {file_ext!r}')

        # Test __delitem__
        raised = False
        ext = 'tiff'
        try:
            del container['tiff']
        except ValueError:
            raised = False
        self.assertFalse(raised, f'Unable to delete specified value: {ext!r}')

        with self.assertRaises(KeyError):
            del container['tiff']

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_properties(self, fake_isfile):
        """FileSequenceContainer: Test class properties."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq = self._input_seqs[0]
        parser.scan_path([str(x) for x in input_seq])
        container = parser.sequences[input_seq.path][input_seq.name]

        self.assertEqual(container.path, input_seq.path)
        self.assertEqual(container.name, input_seq.name)


###############################################################################
# Class: TestFileExtension


class TestFileExtension(unittest.TestCase):
    """Test the FileExtension class used by the Seqparse module."""

    _test_ext = 'exr'
    _test_file_name1 = 'kitty'
    _test_file_name2 = 'cat'
    _test_root = '/pretty/kitty'.replace('/', os.sep)

    def setUp(self):
        """Set up the test case."""
        frames1 = list(range(0, 5))
        frames2 = list(range(1, 6))

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

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_properties(self, fake_isfile):
        """FileExtension: Test class properties."""
        fake_isfile.return_value = True

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq = self._input_seqs[0]
        parser.scan_path([str(x) for x in input_seq])
        container = parser.sequences[input_seq.path][input_seq.name]

        file_ext = container[self._test_ext]
        self.assertEqual(input_seq.ext, file_ext.name)

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_membership(self, fake_isfile):
        """FileExtension: Test membership setting, deletion."""
        fake_isfile.return_value = True
        frames1 = [1, 2, 3, 10, 11, 12, 100, 101, 102]
        full_name = os.path.join(self._test_root, self._test_file_name1)

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq1 = FileSequence(ext=self._test_ext,
                                  frames=frames1,
                                  name=full_name)
        parser.scan_path([str(x) for x in input_seq1])
        container = parser.sequences[input_seq1.path][input_seq1.name]

        file_ext = container[self._test_ext]

        # Test __setitem__, __delitem__ ...
        frames4 = list(range(1000, 1003))
        input_seq4 = FileSequence(ext=self._test_ext,
                                  frames=frames4,
                                  name=full_name)

        for test_input in (frames4, input_seq4):
            raised = False
            blurb = ''
            try:
                file_ext[4] = test_input
                del file_ext[4]
            except KeyError:
                raised = False
                blurb = 'Unable to delete specified value: {!r}'
            except ValueError:
                raised = False
                blurb = 'Unable to set specified value: {!r}'

            self.assertFalse(raised, blurb.format(test_input))

        with self.assertRaises(KeyError):
            del file_ext[4]

        with self.assertRaises(ValueError):
            file_ext[4] = str(input_seq4)

    @mock.patch('seqparse.seqparse.os.path.isfile')
    def test_output(self, fake_isfile):
        """FileExtension: Verify sequence output."""
        fake_isfile.return_value = True
        frames1 = [1, 2, 3, 10, 11, 12, 100, 101, 102]
        full_name = os.path.join(self._test_root, self._test_file_name1)

        parser = get_parser()

        # Add in the source FileSequence files one-by-one.
        input_seq1 = FileSequence(ext=self._test_ext,
                                  frames=frames1,
                                  name=full_name)
        parser.scan_path([str(x) for x in input_seq1])
        container = parser.sequences[input_seq1.path][input_seq1.name]

        file_ext = container[self._test_ext]
        output = '\n'.join(str(x) for x in file_ext.output())

        self.assertEqual(output, str(input_seq1))
