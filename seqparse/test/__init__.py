"""Test suite for seqparse."""

import os

__all__ = ("generate_files", "mock_walk_deep")

###############################################################################
# EXPORTED METHODS


def generate_files(name="dog", ext="jpg", frames=None):
    """Generate some file sequences for seqparse testing."""
    if frames is None:
        frames = {4: [0]}

    file_names = set()

    for pad, frame_list in frames.iteritems():
        for frame in frame_list:
            file_names.add("%s.%0*d.%s" % (name, pad, frame, ext))

    # Casting the set() to a list() so that we're pretty much guaranteed a non-
    # sorted list of files.
    return list(file_names)


def mock_walk_deep(search_path="."):
    """A mocked version of scandir.walk for testing purposes."""
    frames = {4: [0, 1, 2, 3, 4]}
    level1_path = os.path.join(search_path, "level1")
    level2_path = os.path.join(level1_path, "level2")
    level3_path = os.path.join(level2_path, "level3")

    level0_files = generate_files(ext="exr", frames=frames, name="level0_1")
    level0_files.extend(
        generate_files(ext="exr", frames=frames, name="level0_2"))
    level1_files = generate_files(ext="exr", frames=frames, name="level1")
    level2_files = generate_files(ext="exr", frames=frames, name="level2")
    level3_files = generate_files(ext="exr", frames=frames, name="level3")

    return_value = [(search_path, ["level1"], level0_files),
                    (level1_path, ["level2"], level1_files),
                    (level2_path, ["level3"], level2_files),
                    (level3_path, [], level3_files)]

    dir_names = list()
    for index, entry in enumerate(return_value):
        if index and not dir_names:
            raise StopIteration

        del dir_names[:]
        dir_names.extend(entry[1])
        root, file_names = entry[0], entry[2]
        yield root, dir_names, file_names
