"""
Calls that must type-check under `mypy --strict`.

This module is only type-checked (by `mypy`, see pyproject.toml), never run:
it keeps the public signatures usable with the types people really have.
"""

import pathlib

from seqparse import seqparse, sequences


def scan_path_accepts_single_paths(parser: seqparse.Seqparse) -> None:
    """A str, a Path."""
    parser.scan_path("shots")
    parser.scan_path(pathlib.Path("shots"))


def scan_path_accepts_the_usual_collections(
    parser: seqparse.Seqparse,
    names: list[str],
    dirs: list[pathlib.Path],
    seen: set[str],
    pair: tuple[str, str],
) -> None:
    """list, set, tuple and frozenset of str and of paths."""
    parser.scan_path(names)
    parser.scan_path(dirs)
    parser.scan_path(seen)
    parser.scan_path(frozenset(seen))
    parser.scan_path(pair)
    parser.scan_path(["a", pathlib.Path("b")])


def file_sequence_accepts_paths(path: pathlib.Path) -> sequences.FileSequence:
    """A Path is a name like any other."""
    return sequences.FileSequence(name=path, ext="exr")
