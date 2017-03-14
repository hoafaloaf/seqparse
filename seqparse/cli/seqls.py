#!/usr/bin/env python
"""Command line tool for listing file sequences."""

# Standard Libraries
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter

from seqparse import get_parser


def seqls(search_path=None, level=0):
    """Wrap and initialise the seqparse class."""
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

    for output in seqs.output():
        print output


def main():
    """Main entry point to the seqls script."""
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        "search_path",
        default=["."],
        help=("Paths that you'd like to search for file sequences."),
        nargs="*")

    parser.add_argument(
        "-l",
        "--level",
        default=0,
        help=("Maximum number of levels that you'd like to search. Values "
              "less than zero are equivalent to infinite depth."),
        nargs=1,
        required=False)

    # Parse the arguments.
    args = parser.parse_args()

    sys.exit(seqls(**vars(args)))


if __name__ == "__main__":
    main()
