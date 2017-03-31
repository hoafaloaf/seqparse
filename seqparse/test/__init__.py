"""Test suite for seqparse."""

# Standard Libraries
import os
from posix import stat_result

__all__ = ("DirEntry", "generate_entries", "initialise_mock_scandir_data",
           "mock_scandir_deep")

MOCK_SCANDIR_DEEP_DATA = list()

MOCK_SCANDIR_STAT_DATA = {
    'test.0001.py': [
        33279L, 12666373952092765L, 14L, 1L, 0L, 0L, 7975L, 1490908305,
        1490908305, 1490908313
    ],
    'test.0002.py': [
        33279L, 2814749767415947L, 14L, 1L, 0L, 0L, 987L, 1490908305,
        1490908305, 1490908318
    ],
    'test.0003.py': [
        33279L, 2251799813994636L, 14L, 1L, 0L, 0L, 2561L, 1490908305,
        1490908305, 1490908325
    ],
    'test.0004.py': [
        33279L, 2251799813994637L, 14L, 1L, 0L, 0L, 6487L, 1490908305,
        1490908305, 1490908333
    ],
    'test.0006.py': [
        33279L, 2251799813994638L, 14L, 1L, 0L, 0L, 18510L, 1490908305,
        1490908305, 1490908340
    ],
    'pony.py': [
        33279L, 36028797019078328L, 14L, 1L, 0L, 0L, 9436L, 1490997828,
        1490997828, 1490997828
    ]
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
        return stat_result(MOCK_SCANDIR_STAT_DATA[self.name])


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
