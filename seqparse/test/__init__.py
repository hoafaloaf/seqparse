"""Test suite for seqparse."""

__all__ = ("generate_files", )

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
