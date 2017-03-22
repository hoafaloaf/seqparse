#!/usr/bin/env python
"""Command line tool for listing file sequences."""

# Standard Libraries
import os
import sys
from argparse import ArgumentParser

from .. import get_parser


def _entry_point():  # pragma: no cover
    """Main entry point into the script."""
    main(parse_args(sys.argv[1:]))


def main(args, _debug=False):
    """Wrap and initialise the Seqparse class."""
    args.level = max(int(args.level[0]), 0)

    for search_path in sorted(args.search_path):
        search_path = os.path.abspath(search_path)
        seqs = get_parser()
        seqs.scan_path(search_path, level=args.level)

    output = seqs.output(missing=args.missing, seqs_only=args.seqs_only)
    if _debug:
        return map(str, output)

    else:  # pragma: no cover
        print
        for line in output:
            print line


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

    parser.add_argument(
        "-m",
        "--missing",
        action="store_true",
        help=("Whether to invert output file sequences to only report the"
              "missing frames."))

    parser.add_argument(
        "-S",
        "--seqs_only",
        action="store_true",
        help="Whether to filter out all non-sequence files.")

    # Parse the arguments.
    return parser.parse_args(args)


if __name__ == "__main__":
    _entry_point()
    sys.exit(0)
