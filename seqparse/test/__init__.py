"""Test suite for seqparse."""

import os

__all__ = ("DirEntry", "generate_entries", "initialise_mock_scandir_data",
           "mock_scandir_deep")

MOCK_SCANDIR_DEEP_DATA = list()

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

    def is_dir(self, *args, **kwargs):
        """Whether this instance represents a directory."""
        return not self._is_file

    def is_file(self, *args, **kwargs):
        """Whether this instance represents a file."""
        return self._is_file


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
    global MOCK_SCANDIR_DEEP_DATA

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


def mock_scandir_deep(search_path="."):
    """A mocked version of scandir.scandir for testing purposes."""
    global MOCK_SCANDIR_DEEP_DATA

    if MOCK_SCANDIR_DEEP_DATA:
        return_value = MOCK_SCANDIR_DEEP_DATA.pop(0)
    else:
        raise StopIteration

    for entry in return_value:
        yield entry
