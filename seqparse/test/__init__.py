"""Test suite for seqparse."""

import os

__all__ = ("DirEntry", "generate_entries", "initialise_mock_scandir_data",
           "mock_scandir_deep")

MOCK_SCANDIR_DEEP_DATA = list()

MOCK_SCANDIR_STAT_DATA = {
    'test.0001.py': {
        'm_size': 7975L,
        'm_uid': 0L,
        'm_dev': 14L,
        'm_nlink': 1L,
        'm_gid': 0L,
        'm_mode': 33279L,
        'm_mtime': 1490908305,
        'm_atime': 1490908305,
        'm_ino': 12666373952092765L,
        'm_ctime': 1490908313
    },
    'test.0002.py': {
        'm_size': 987L,
        'm_uid': 0L,
        'm_dev': 14L,
        'm_nlink': 1L,
        'm_gid': 0L,
        'm_mode': 33279L,
        'm_mtime': 1490908305,
        'm_atime': 1490908305,
        'm_ino': 2814749767415947L,
        'm_ctime': 1490908318
    },
    'test.0003.py': {
        'm_size': 2561L,
        'm_uid': 0L,
        'm_dev': 14L,
        'm_nlink': 1L,
        'm_gid': 0L,
        'm_mode': 33279L,
        'm_mtime': 1490908305,
        'm_atime': 1490908305,
        'm_ino': 2251799813994636L,
        'm_ctime': 1490908325
    },
    'test.0004.py': {
        'm_size': 6487L,
        'm_uid': 0L,
        'm_dev': 14L,
        'm_nlink': 1L,
        'm_gid': 0L,
        'm_mode': 33279L,
        'm_mtime': 1490908305,
        'm_atime': 1490908305,
        'm_ino': 2251799813994637L,
        'm_ctime': 1490908333
    },
    'test.0006.py': {
        'm_size': 18510L,
        'm_uid': 0L,
        'm_dev': 14L,
        'm_nlink': 1L,
        'm_gid': 0L,
        'm_mode': 33279L,
        'm_mtime': 1490908305,
        'm_atime': 1490908305,
        'm_ino': 2251799813994638L,
        'm_ctime': 1490908340
    }
}

###############################################################################
# EXPORTED CLASSES


class DirEntry(object):
    """Mocked DirEntry class."""

    def __init__(self, file_path, is_file=True):
        """Initialise the instance."""
        self.name = os.path.basename(file_path)
        self.path = file_path
        self._is_file = is_file

    def __repr__(self):
        """A representation for the instance."""
        blurb = "{}(path={!r}, is_file={!r})"
        return blurb.format(type(self).__name__, self.path, self.is_file())

    def is_dir(self, follow_symlinks=False):  # pylint: disable=W0613
        """Whether this instance represents a directory."""
        return not self._is_file

    def is_file(self, follow_symlinks=False):  # pylint: disable=W0613
        """Whether this instance represents a file."""
        return self._is_file

    def stat(self, follow_symlinks=False):  # pylint: disable=W0613
        """Return mock'd os.stat object for the given file."""
        if self.name not in MOCK_SCANDIR_STAT_DATA:
            raise IOError("Mock'd file not found: {}".format(self.name))

        mock_stat = object()
        for attr, val in MOCK_SCANDIR_STAT_DATA.iteritems():
            setattr(mock_stat, attr, val)

        return mock_stat


###############################################################################
# EXPORTED METHODS


def generate_entries(name="dog",
                     ext="jpg",
                     frames=None,
                     root=".",
                     is_file=True):
    """Generate some file sequences for seqparse testing."""
    if frames is None:
        frames = {4: [0, 1, 2, 3, 4]}

    file_entries = set()

    for pad, frame_list in frames.iteritems():
        for frame in frame_list:
            file_name = "{}.{:0{}d}.{}".format(name, frame, pad, ext)
            file_entries.add(
                DirEntry(os.path.join(root, file_name), is_file=is_file))

    # Casting the set() to a list() so that we're pretty much guaranteed a non-
    # sorted list of files.
    return list(file_entries)


def initialise_mock_scandir_data(search_path):
    """Initialise the global variable accessed by mock_scandir_deep."""
    global MOCK_SCANDIR_DEEP_DATA  # pylint: disable=W0602

    level1_path = os.path.join(search_path, "level1")
    level2_path = os.path.join(level1_path, "level2")
    level3_path = os.path.join(level2_path, "level3")

    level0_entries = generate_entries(
        ext="exr", name="level0_1", root=search_path)
    level0_entries.extend(
        generate_entries(ext="exr", name="level0_2", root=search_path))
    level0_entries.append(DirEntry(level1_path, is_file=False))
    level1_entries = generate_entries(
        ext="exr", name="level1", root=level1_path)
    level1_entries.append(DirEntry(level2_path, is_file=False))
    level2_entries = generate_entries(
        ext="exr", name="level2", root=level2_path)
    level2_entries.append(DirEntry(level3_path, is_file=False))
    level3_entries = generate_entries(
        ext="exr", name="level3", root=level3_path)

    del MOCK_SCANDIR_DEEP_DATA[:]
    MOCK_SCANDIR_DEEP_DATA.extend(
        (level0_entries, level1_entries, level2_entries, level3_entries))


def mock_scandir_deep(search_path="."):  # pylint: disable=W0613
    """A mocked version of scandir.scandir for testing purposes."""
    global MOCK_SCANDIR_DEEP_DATA  # pylint: disable=W0602

    if MOCK_SCANDIR_DEEP_DATA:
        return_value = MOCK_SCANDIR_DEEP_DATA.pop(0)
    else:
        raise StopIteration

    for entry in return_value:
        yield entry
