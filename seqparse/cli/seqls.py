#!/usr/bin/env python
"""Command line tool for listing file sequences."""

# Standard Libraries
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter

from .. import get_parser


def _entry_point():  #pragma: no cover
    """Main entry point into the script."""
    args = vars(parse_args(sys.argv[1:]))
    main(**args)


def main(search_path=None, level=0, _debug=False):
    """Wrap and initialise the Seqparse class."""
    if not search_path:
        search_paths = ["."]
    elif isinstance(search_path, (list, set, tuple)):
        search_paths = search_path
    else:
        search_paths = [search_path]

    if isinstance(level, (list, set, tuple)):
        level = level[0]

    level = max(int(level), 0)

    for search_path in sorted(search_paths):
        search_path = os.path.abspath(search_path)
        seqs = get_parser()
        seqs.scan_path(search_path, level=level)

    if _debug:
        return list(seqs.output())

    for output in seqs.output():  # pragma: no cover
        print output


def parse_args(args):
    """Parse any input arguments."""
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        "search_path",
        default=["."],
        help=("Paths that you'd like to search for file sequences."),
        nargs="*")

    parser.add_argument(
        "-l",
        "--level",
        default=["0"],
        help=("Maximum number of levels that you'd like to search. Values "
              "less than zero are equivalent to infinite depth."),
        nargs=1,
        required=False)

    # Parse the arguments.
    return parser.parse_args(args)


if __name__ == "__main__":
    _entry_point()
    sys.exit(0)
