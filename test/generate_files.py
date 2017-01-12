#!/usr/bin/env python
"""Generate a bunch of numbered files for Jakub."""

import os
import sys


def generate_files(loc=None, name="dog", ext="jpg"):
    """Generate some file sequences for Jakub's Python training ..."""
    if loc is None:
        loc = "."
    loc = os.path.abspath(loc)

    if not os.path.exists(loc):
        print "Creating test location:"
        print "   ", loc
        os.makedirs(loc)

    # Frame numbers for the "dog" .jpg files we'll be creating.
    frames = {
        4: [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 101],
        3: [8, 9, 10, 12],
        0: [5, 6, 7, 8, 114, 199, 2000]
    }

    for pad, frame_list in sorted(frames.items()):
        for frame in frame_list:
            file_name = os.path.join(loc, "%s.%0*d.%s" %
                                     (name, pad, frame, ext))
            if not os.path.exists(file_name):
                print "Creating:", file_name
                open(file_name, "a").close()

    # "0" is good; it means nothing's broken!
    return 0


if __name__ == "__main__":
    sys.exit(generate_files(*sys.argv[1:]))
