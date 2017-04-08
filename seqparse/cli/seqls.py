#!/usr/bin/env python
"""
Command line tool for listing file sequences.

Upon installation of the package this script will be accessable via `seqls`
command on the command line of your choice.
"""

# "Future" Libraries
from __future__ import print_function

# Standard Libraries
import os
import sys
import time
from argparse import ArgumentParser

# Third Party Libraries
import humanize

from .. import get_parser, get_version


def run_main():  # pragma: no cover
    """Main entry point into the script."""
    main(parse_args(sys.argv[1:]))


def main(args, _debug=False):
    """Wrap and initialise the Seqparse class."""
    if args.version:
        # Print the version and exit.
        if _debug:
            return get_version(pretty=True)
        else:  # pragma: no cover
            print(get_version(pretty=True))
            return

    if args.max_levels[0] != -1:
        args.max_levels[0] = max(args.max_levels[0], 0)
    if args.min_levels[0] != -1:
        args.min_levels[0] = max(args.min_levels[0], 0)

    scan_opts = dict(
        max_levels=args.max_levels[0], min_levels=args.min_levels[0])

    parser = get_parser()
    parser.scan_options.update(all=args.all, stat=args.long_format)

    for search_path in sorted(args.search_path):
        search_path = os.path.abspath(search_path)
        parser.scan_path(search_path, **scan_opts)

    output = list()

    items = parser.output(missing=args.missing, seqs_only=args.seqs_only)
    if args.long_format:
        output.extend(long_format_output(items, args.human_readable))
    else:
        output.extend(str(x) for x in items)

    if _debug:
        return output

    else:  # pragma: no cover
        print("")
        for line in output:
            print(line)


def long_format_output(items, human_readable=False):
    """Generate long format output for the provided items."""
    bits = list()
    output = list()

    for item in items:
        size = item.size
        if size:
            size = item.size
            if human_readable:
                size = humanize.naturalsize(size, gnu=True)
        else:
            size = "----"

        mtime = time.strftime('%Y/%m/%d %H:%M', time.localtime(item.mtime))
        bits.append((size, mtime, str(item)))

    # Find the maximum width of the sequence sizes; we'll use this to pad
    # the output.
    if bits:
        max_len = max(len(str(x[0])) for x in bits)
        for bit in bits:
            output.append("{:<{:d}}  {}  {}".format(bit[0], max_len, *bit[1:]))

    return output


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
        help=("with -l/--long, print sizes in human readable format (e.g., 1K "
              "234M 2G)."))

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
              "scan the starting-points themselves."),
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
        help=("Whether to invert output file sequences to only report the "
              "missing frames."))

    parser.add_argument(
        "-S",
        "--seqs-only",
        action="store_true",
        dest="seqs_only",
        help="Whether to filter out all non-sequence files.")

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print the version and exit.")

    # Parse the arguments.
    parsed_args = parser.parse_args(args)

    # We'll assume that if the user is requesting missing sequence files that
    # he/she doesn't want to see any singletons.
    if parsed_args.missing:
        parsed_args.seqs_only = True

    return parsed_args


if __name__ == "__main__":
    run_main()
    sys.exit(0)
