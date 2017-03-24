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
    if args.max_levels[0] != -1:
        args.max_levels[0] = max(int(args.max_levels[0]), 0)
    if args.min_levels[0] != -1:
        args.min_levels[0] = max(int(args.min_levels[0]), 0)

    for search_path in sorted(args.search_path):
        search_path = os.path.abspath(search_path)
        seqs = get_parser()
        seqs.scan_path(
            search_path,
            max_levels=args.max_levels[0],
            min_levels=args.min_levels[0])

    output = seqs.output(missing=args.missing, seqs_only=args.seqs_only)
    if _debug:
        return map(str, output)

    else:  # pragma: no cover
        print
        for file_name in output:
            print file_name


def parse_args(args):
    """Parse any input arguments."""
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        "search_path",
        default=["."],
        help=("Paths that you'd like to search for file sequences."),
        nargs="*")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Do not ignore entries starting with '.'.")

    parser.add_argument(
        "-H",
        "--human-readable",
        action="store_true",
        dest="human_readable",
        help=("with -l, print sizes in human readable format (e.g., 1K 234M "
              "2G)."))

    parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        dest="long_format",
        help="Use a long listing format.")

    parser.add_argument(
        "--maxdepth",
        default=[-1],
        dest="max_levels",
        help=("Descend at most levels (a non-negative integer) MAX_LEVELS of "
              "directories below the starting-points. '--maxdepth 0' means "
              "apply scan the starting-points themselves."),
        nargs=1,
        required=False,
        type=int)

    parser.add_argument(
        "--mindepth",
        default=[-1],
        dest="min_levels",
        help=("Do not scan at levels less than MIN_LEVELS (a non-negative "
              "integer). '--mindepth 1' means scan all levels except the "
              " starting-points."),
        nargs=1,
        required=False,
        type=int)

    parser.add_argument(
        "-m",
        "--missing",
        action="store_true",
        help=("Whether to invert output file sequences to only report the"
              "missing frames."))

    parser.add_argument(
        "-S",
        "--seqs-only",
        action="store_true",
        dest="seqs_only",
        help="Whether to filter out all non-sequence files.")

    # Parse the arguments.
    return parser.parse_args(args)


if __name__ == "__main__":
    _entry_point()
    sys.exit(0)
