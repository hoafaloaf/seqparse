#!/usr/bin/env python
"""
Command line tool for listing file sequences.

Upon installation of the package this script will be accessible via `seqls`
command on the command line of your choice.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Iterator, Sequence
import json
import os
import sys
import time
from typing import Any

import humanize

import seqparse
from seqparse import files, sequences
from seqparse import seqparse as seqparse_module

__all__ = (
    "json_output",
    "long_format_output",
    "main",
    "parse_args",
    "run_main",
)


def run_main() -> None:  # pragma: no cover
    """Main entry point into the script."""
    main(parse_args(sys.argv[1:]))


def main(
    args: argparse.Namespace,
    _debug: bool = False,
    stdin: Iterable[str] | None = None,
) -> str | list[str] | None:
    """
    Wrap and initialise the Seqparse class.

    Args:
        args: Parsed command line arguments (see `parse_args`).
        _debug (bool, optional): Return the result instead of printing it.
        stdin (iterable of str, optional): The lines to read file names from
            when the search paths include "-". Defaults to sys.stdin.
    """
    if args.version:
        # Print the version and exit.
        if _debug:
            return seqparse.get_version(pretty=True)
        print(seqparse.get_version(pretty=True))
        return None

    parser = _load(args, sys.stdin if stdin is None else stdin)

    if args.json:
        text = json_output(
            parser.output(seqs_only=args.seqs_only),
            only_missing=args.missing,
            only_empty=args.empty,
        )
        if _debug:
            return text
        print(text)
        return None

    output = _text_lines(parser, args)
    if _debug:
        return output

    print("")
    for line in output:
        print(line)

    return None


def _load(
    args: argparse.Namespace, stdin: Iterable[str]
) -> seqparse_module.Seqparse:
    """Scan the search paths and read any names from stdin."""
    if args.max_levels[0] != -1:
        args.max_levels[0] = max(args.max_levels[0], 0)
    if args.min_levels[0] != -1:
        args.min_levels[0] = max(args.min_levels[0], 0)

    scan_opts = {
        "max_levels": args.max_levels[0],
        "min_levels": args.min_levels[0],
    }

    parser = seqparse.get_parser()
    parser.scan_options.update(
        {"all": args.all, "stat": args.long_format or args.empty}
    )

    for search_path in sorted(p for p in args.search_path if p != "-"):
        parser.scan_path(os.path.abspath(search_path), **scan_opts)

    if "-" in args.search_path:
        for name in _read_names(stdin):
            parser.add_file(name)

    return parser


def _text_lines(
    parser: seqparse_module.Seqparse, args: argparse.Namespace
) -> list[str]:
    """The lines of text output for what the parser found."""
    items = parser.output(missing=args.missing, seqs_only=args.seqs_only)
    if args.empty:
        items = _empty_files(items)
    if args.long_format:
        return long_format_output(items, args.human_readable)
    return [str(x) for x in items]


def _read_names(lines: Iterable[str]) -> Iterator[str]:
    """Yield the file names in the lines, skipping blank ones."""
    for line in lines:
        name = line.rstrip("\r\n")
        if name.strip():
            yield name


def _empty_files(
    items: Iterable[files.File | sequences.FileSequence],
) -> Iterator[sequences.FileSequence]:
    """Yield the zero-byte files of each sequence that has any."""
    for item in items:
        if isinstance(item, sequences.FileSequence):
            empty = item.empty_files()
            if empty:
                yield empty


def json_output(
    items: Iterable[files.File | sequences.FileSequence],
    only_missing: bool = False,
    only_empty: bool = False,
) -> str:
    """
    Describe the items as a JSON array.

    Args:
        items: The files and file sequences to describe.
        only_missing (bool, optional): Only describe sequences that have
            missing frames (singletons are left out). Defaults to False.
        only_empty (bool, optional): Only describe sequences that have
            zero-byte files (singletons are left out). Defaults to False.

    Returns:
        JSON text; see the README for the fields. Sizes, times and empty
        files are null unless the items were scanned with disk stats.
    """
    records: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, sequences.FileSequence):
            if not (only_missing or only_empty):
                records.append(
                    {
                        "type": "file",
                        "path": item.path,
                        "name": item.name,
                        "size": item.size,
                        "mtime": item.mtime,
                        "string": str(item),
                    }
                )
            continue

        missing = item.invert().pretty_frames
        if only_missing and not missing:
            continue

        # Without disk stats there is nothing to tell (as opposed to "none").
        empty = item.empty_files().pretty_frames if item.stat() else None
        if only_empty and not empty:
            continue

        first = last = 0
        for number, frame in enumerate(item.frames):
            if number == 0:
                first = int(frame)
            last = int(frame)

        records.append(
            {
                "type": "sequence",
                "path": item.path,
                "name": item.name,
                "ext": item.ext,
                "pad": item.pad,
                "frames": item.pretty_frames,
                "count": len(item),
                "first": first,
                "last": last,
                "missing": missing,
                "empty": empty,
                "size": item.size,
                "mtime": item.mtime,
                "string": str(item),
            }
        )

    return json.dumps(records, indent=2)


def long_format_output(
    items: Iterable[files.File | sequences.FileSequence],
    human_readable: bool = False,
) -> list[str]:
    """Generate long format output for the provided items."""
    bits = []
    output = []

    for item in items:
        size: int | str | None = item.size
        if size is None:
            size = "----"
        elif human_readable:
            size = humanize.naturalsize(size, gnu=True)

        mtime = "----"
        if item.mtime is not None:
            mtime = time.strftime("%Y/%m/%d %H:%M", time.localtime(item.mtime))
        bits.append((size, mtime, str(item)))

    # Find the maximum width of the sequence sizes; we'll use this to pad
    # the output.
    if bits:
        max_len = max(len(str(x[0])) for x in bits)
        for bit in bits:
            output.append(f"{bit[0]:<{max_len:d}}  {bit[1]}  {bit[2]}")

    return output


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    """Parse any input arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "search_path",
        default=["."],
        help=(
            "Paths that you'd like to search for file sequences. Use '-' to "
            "read file names (one per line) from standard input instead; "
            "they are used as written, so -a, --maxdepth and --mindepth do "
            "not apply to them."
        ),
        nargs="*",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Do not ignore entries starting with '.'.",
    )

    parser.add_argument(
        "-H",
        "--human-readable",
        action="store_true",
        dest="human_readable",
        help=(
            "with -l/--long, print sizes in human readable format (e.g., 1K "
            "234M 2G)."
        ),
    )

    parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        dest="long_format",
        help="Use a long listing format.",
    )

    parser.add_argument(
        "--maxdepth",
        default=[-1],
        dest="max_levels",
        help=(
            "Descend at most MAX_LEVELS (a non-negative integer) levels of "
            "directories below the starting points; 0 scans only the "
            "starting points themselves."
        ),
        nargs=1,
        required=False,
        type=int,
    )

    parser.add_argument(
        "--mindepth",
        default=[-1],
        dest="min_levels",
        help=(
            "Do not scan at levels less than MIN_LEVELS (a non-negative "
            "integer); 1 scans every level except the starting points."
        ),
        nargs=1,
        required=False,
        type=int,
    )

    problems = parser.add_mutually_exclusive_group()
    problems.add_argument(
        "-m",
        "--missing",
        action="store_true",
        help=(
            "Whether to invert output file sequences to only report the "
            "missing frames."
        ),
    )
    problems.add_argument(
        "--empty",
        action="store_true",
        help=(
            "Only report the zero-byte frames of each sequence (the likely "
            "debris of a crashed render), as a frame sequence."
        ),
    )

    parser.add_argument(
        "-S",
        "--seqs-only",
        action="store_true",
        dest="seqs_only",
        help="Whether to filter out all non-sequence files.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Print JSON instead of text: sizes (bytes) and modification "
            "times (epoch seconds) are included with -l/--long, and with "
            "-m/--missing only sequences that have gaps are listed."
        ),
    )

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print the version and exit.",
    )

    # Parse the arguments.
    parsed_args = parser.parse_args(args)

    # Names from stdin need not exist, so there is nothing to stat.
    if "-" in parsed_args.search_path and (
        parsed_args.long_format or parsed_args.empty
    ):
        parser.error(
            "-l/--long and --empty need files on disk, not names from stdin"
        )

    # We'll assume that if the user is requesting missing (or empty) sequence
    # files that he/she doesn't want to see any singletons.
    if parsed_args.missing or parsed_args.empty:
        parsed_args.seqs_only = True

    return parsed_args


if __name__ == "__main__":
    run_main()
    sys.exit(0)
