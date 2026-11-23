#!/usr/bin/env python
"""
Command line tools for copying (`seqcp`) and moving (`seqmv`) file sequences.

Renumbering is a move that stays in the same directory: `seqmv --offset 1000
plate.0001-0100.exr`. Nothing is overwritten unless `--force` is given, and
everything is checked before the first file is touched (see `seqparse.transfer`
for the rules).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys
from typing import TextIO

from seqparse import seqparse as seqparse_module
from seqparse import sequences, transfer

__all__ = ("main", "parse_args", "run_cp", "run_mv")

# A long sequence with a common problem would print thousands of lines.
_MAX_PROBLEMS = 10


def run_cp() -> None:  # pragma: no cover
    """Entry point of the seqcp command."""
    sys.exit(main(parse_args(sys.argv[1:], copy=True), copy=True))


def run_mv() -> None:  # pragma: no cover
    """Entry point of the seqmv command."""
    sys.exit(main(parse_args(sys.argv[1:], copy=False), copy=False))


def parse_args(args: Sequence[str], copy: bool) -> argparse.Namespace:
    """
    Parse the command line.

    Args:
        args: The arguments (without the program name).
        copy (bool): Whether this is seqcp (True) or seqmv (False).
    """
    verb = "copy" if copy else "move"
    parser = argparse.ArgumentParser(
        prog="seqcp" if copy else "seqmv",
        description=(
            f"{verb.capitalize()} a file sequence, optionally renumbering or "
            "renaming it. Nothing is overwritten unless --force is given, and "
            "everything is checked before the first file is touched."
        ),
    )
    parser.add_argument(
        "source",
        help=(
            f"The file sequence to {verb}, in the usual notation (eg "
            "/shots/a/plate.0001-0100.exr); a range of frames is allowed."
        ),
    )
    parser.add_argument(
        "dest",
        nargs="?",
        help=(
            "The directory to put the files in (default: the source's own "
            "directory)."
        ),
    )
    numbering = parser.add_mutually_exclusive_group()
    numbering.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Add this to every frame number (it may be negative).",
    )
    numbering.add_argument(
        "--start",
        type=int,
        help="Renumber so that the first frame becomes this (gaps are kept).",
    )
    parser.add_argument("--name", help="A new base name for the sequence.")
    parser.add_argument(
        "--pad", type=int, help="Zero-padding for the new frame numbers."
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Replace files that already exist.",
    )
    parser.add_argument(
        "-p",
        "--parents",
        action="store_true",
        help="Create the destination directory if it does not exist.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Only show what would be done.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="List every file as it is processed.",
    )
    return parser.parse_args(args)


def _files(count: int) -> str:
    """Describe a number of files, eg "1 file" or "2 files"."""
    return f"{count} file" if count == 1 else f"{count} files"


def _source(text: str) -> sequences.FileSequence | None:
    """The one file sequence the text describes (None if it is not one)."""
    parser = seqparse_module.Seqparse()
    parser.add_file(text)
    found = list(parser.output(seqs_only=True))
    if len(found) != 1 or not isinstance(found[0], sequences.FileSequence):
        return None
    return found[0]


def _make_plan(
    args: argparse.Namespace, copy: bool, err: TextIO
) -> tuple[sequences.FileSequence, transfer.Plan] | None:
    """The plan for the command line; None (after saying why) if impossible."""
    prog = "seqcp" if copy else "seqmv"
    fseq = _source(args.source)
    if fseq is None:
        print(f"{prog}: not a file sequence: {args.source}", file=err)
        return None
    plan_for = transfer.plan_copy if copy else transfer.plan_move
    try:
        plan = plan_for(
            fseq,
            args.dest,
            name=args.name,
            offset=args.offset,
            start=args.start,
            pad=args.pad,
            overwrite=args.force,
            parents=args.parents,
        )
    except ValueError as error:
        print(f"{prog}: {error}", file=err)
        return None
    for problem in plan.problems[:_MAX_PROBLEMS]:
        print(f"{prog}: {problem}", file=err)
    hidden = len(plan.problems) - _MAX_PROBLEMS
    if hidden > 0:
        print(f"{prog}: ... and {hidden} more problems", file=err)
    return None if plan.problems else (fseq, plan)


def main(
    args: argparse.Namespace,
    copy: bool,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """
    Run seqcp or seqmv.

    Args:
        args: Parsed arguments (see `parse_args`).
        copy (bool): Whether to copy (True) or move (False).
        out (TextIO, optional): Where to print results. Defaults to stdout.
        err (TextIO, optional): Where to print problems. Defaults to stderr.

    Returns:
        The exit status: 0 for success, 1 for a problem or a failure.
    """
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    prog = "seqcp" if copy else "seqmv"

    made = _make_plan(args, copy, err)
    if made is None:
        return 1
    fseq, plan = made
    if not plan.pairs:
        print("nothing to do", file=out)
        return 0

    if args.dry_run or args.verbose:
        for src, dst in plan.pairs:
            print(f"{src} -> {dst}", file=out)
    summary = f"{_files(len(plan.pairs))}: {fseq} -> {plan.result}"
    if args.dry_run:
        print(f"would {'copy' if copy else 'move'} {summary}", file=out)
        return 0

    try:
        plan.execute()
    except transfer.TransferError as error:
        print(f"{prog}: {error}", file=err)
        if error.rolled_back:
            print(f"{prog}: everything done so far was undone", file=err)
        for problem in error.rollback_errors:
            print(f"{prog}: {problem}", file=err)
        return 1
    print(f"{'copied' if copy else 'moved'} {summary}", file=out)
    return 0
