"""
Copy, move and renumber the files of a file sequence.

Everything goes through a plan: `plan_move` and `plan_copy` look at the disk
and report what they would do (`Plan.pairs`) and what stands in the way
(`Plan.problems`) without touching a file. `Plan.execute` then does the work.

```python
from seqparse import seqparse, transfer

parser = seqparse.Seqparse()
parser.add_file("/shots/a/plate.0001-0100.exr")
(fseq,) = parser.output(seqs_only=True)

plan = transfer.plan_move(fseq, offset=1000)  # renumber: 1001-1100
if plan.problems:
    print("\\n".join(plan.problems))
else:
    plan.execute()
```

The safety rules:

1. Nothing is overwritten unless `overwrite` is set. Files are created
   exclusively, so even a file that appears after the plan was made is left
   alone (on a filesystem without hard links a move can only use a plain
   rename, which cannot check). With `overwrite`, a copy is written to a
   temporary file and renamed over the destination: a symlink there is
   replaced, never written through, and a failed copy leaves the old file.
2. Everything is checked before any file is touched: the sources exist, no two
   files go to the same destination, and no destination exists. Names that
   differ only by case collide on case-insensitive filesystems, because the
   check compares the files themselves.
3. When the destinations overlap the sources (a shift within one directory),
   the files are processed in an order that never overwrites a source before it
   has moved: highest frame first for a positive offset. Anything that cannot
   be ordered safely (a swap or rotation) is refused.
4. On an error the transfer stops, and the steps that were already done are
   undone as far as possible. Atomicity is not promised: a file that was
   overwritten (`overwrite=True`) cannot be restored.
5. A move across filesystems copies the file and deletes the original only
   after the copy succeeded.
6. Gaps stay gaps: only the frames of the sequence are transferred.
7. Frame numbers keep the sequence's padding unless `pad` is given; a number
   with more digits than the padding simply uses them.
8. Frame numbers below 0 are refused.
9. Copies keep modification times, and a copied symlink becomes a copy of the
   file it points to. A moved symlink stays a symlink.
"""

from __future__ import annotations

import collections
from collections.abc import Sequence
import contextlib
import dataclasses
import errno
import os
import shutil
import stat
from typing import Any, Literal
import unicodedata

from seqparse import sequences

__all__ = ("Plan", "TransferError", "plan_copy", "plan_move")

_Kind = Literal["copy", "move"]
_Pair = tuple[str, str]


class TransferError(OSError):
    """
    A transfer failed part way through.

    Attributes:
        done (list): The (source, destination) pairs that had completed.
        failed (tuple): The (source, destination) pair that failed.
        rolled_back (bool): Whether everything that was done has been undone.
        rollback_errors (list): What went wrong while undoing (if anything).
    """

    def __init__(
        self,
        message: str,
        done: list[_Pair],
        failed: _Pair,
        rolled_back: bool,
        rollback_errors: list[str],
    ) -> None:
        """Initialise the instance."""
        super().__init__(message)
        self.done = done
        self.failed = failed
        self.rolled_back = rolled_back
        self.rollback_errors = rollback_errors

    def __reduce__(self) -> tuple[Any, ...]:
        """Make the exception picklable and copyable (OSError cannot)."""
        return (
            type(self),
            (
                self.args[0],
                self.done,
                self.failed,
                self.rolled_back,
                self.rollback_errors,
            ),
        )


@dataclasses.dataclass(frozen=True)
class _Options:
    """What the caller asked for."""

    dest: str | None
    name: str | None
    offset: int
    start: int | None
    pad: int | None
    overwrite: bool
    parents: bool


@dataclasses.dataclass(frozen=True)
class _Context:
    """What a plan needs to remember about how it was made."""

    options: _Options
    # Existing files that the transfer replaces (and so cannot give back).
    preexisting: frozenset[str]


class Plan:
    """
    What a copy or move would do; nothing has been touched yet.

    Attributes:
        kind (str): "copy" or "move".
        pairs (list): The (source, destination) file names, in the order in
            which they will be processed.
        problems (list): Everything that stands in the way. The plan can only
            be executed when this is empty.
        result (FileSequence): The sequence as it will be after the transfer.
    """

    def __init__(
        self,
        kind: _Kind,
        pairs: list[_Pair],
        problems: list[str],
        result: sequences.FileSequence,
        context: _Context,
    ) -> None:
        """Initialise the instance."""
        self.kind = kind
        self.pairs = pairs
        self.problems = problems
        self.result = result
        self._context = context

    def __repr__(self) -> str:
        """Pretty representation of the instance."""
        return (
            f"Plan({self.kind}, {len(self.pairs)} files, "
            f"{len(self.problems)} problems)"
        )

    def execute(self) -> sequences.FileSequence:
        """
        Carry out the transfer.

        Returns:
            The transferred sequence (`result`).

        Raises:
            ValueError: If the plan has problems; nothing is touched.
            TransferError: If a file operation fails. The steps that had
                completed are undone as far as possible first.
        """
        if self.problems:
            raise ValueError(
                "cannot run a plan that has problems:\n  "
                + "\n  ".join(self.problems)
            )
        directory = self.result.path
        created: list[str] = []
        if self._context.options.parents and directory:
            created = _make_directories(directory)

        done: list[_Pair] = []
        for pair in self.pairs:
            try:
                self._transfer(*pair)
            except OSError as error:
                errors = self._undo(done)
                _remove_directories(created)
                raise TransferError(
                    f"{self.kind} failed at {pair[0]}: {error}",
                    done,
                    pair,
                    not errors,
                    errors,
                ) from error
            done.append(pair)
        return self.result

    def _transfer(self, src: str, dst: str) -> None:
        """Move or copy one file."""
        overwrite = self._context.options.overwrite
        if self.kind == "move":
            _move_file(src, dst, overwrite)
        else:
            _copy_file(src, dst, overwrite, follow_symlinks=True)

    def _undo(self, done: Sequence[_Pair]) -> list[str]:
        """Undo completed steps (newest first); return what went wrong."""
        errors: list[str] = []
        for src, dst in reversed(done):
            if dst in self._context.preexisting:
                errors.append(f"{dst} was overwritten and cannot be restored")
                continue
            try:
                if self.kind == "move":
                    _move_file(dst, src, overwrite=False)
                else:
                    os.unlink(dst)
            except OSError as error:
                errors.append(f"could not undo {src} -> {dst}: {error}")
        return errors


def plan_move(  # noqa: PLR0913
    fseq: sequences.FileSequence,
    dest: str | os.PathLike[str] | None = None,
    *,
    name: str | None = None,
    offset: int = 0,
    start: int | None = None,
    pad: int | None = None,
    overwrite: bool = False,
    parents: bool = False,
) -> Plan:
    """
    Plan moving (or renaming, or renumbering) the files of a sequence.

    Args:
        fseq (FileSequence): The files to move.
        dest (str, optional): The directory to move them to. Defaults to the
            sequence's own directory.
        name (str, optional): A new base name. Defaults to the current one.
        offset (int, optional): Add this to every frame number.
        start (int, optional): Renumber so that the first frame becomes this
            (gaps are kept). Cannot be combined with `offset`.
        pad (int, optional): Zero-padding for the new frame numbers. Defaults
            to the sequence's padding.
        overwrite (bool, optional): Allow replacing existing files.
        parents (bool, optional): Create the destination directory if it does
            not exist.

    Returns:
        The plan; check `Plan.problems` before calling `Plan.execute`.

    Raises:
        ValueError: For contradictory arguments or frame numbers below 0.
    """
    options = _Options(
        None if dest is None else os.fspath(dest),
        name,
        offset,
        start,
        pad,
        overwrite,
        parents,
    )
    return _plan("move", fseq, options)


def plan_copy(  # noqa: PLR0913
    fseq: sequences.FileSequence,
    dest: str | os.PathLike[str] | None = None,
    *,
    name: str | None = None,
    offset: int = 0,
    start: int | None = None,
    pad: int | None = None,
    overwrite: bool = False,
    parents: bool = False,
) -> Plan:
    """
    Plan copying the files of a sequence (optionally renumbering the copies).

    The arguments are those of `plan_move`.

    Returns:
        The plan; check `Plan.problems` before calling `Plan.execute`.

    Raises:
        ValueError: For contradictory arguments or frame numbers below 0.
    """
    options = _Options(
        None if dest is None else os.fspath(dest),
        name,
        offset,
        start,
        pad,
        overwrite,
        parents,
    )
    return _plan("copy", fseq, options)


###############################################################################
# Planning


def _plan(kind: _Kind, fseq: sequences.FileSequence, options: _Options) -> Plan:
    """Work out what a transfer of the sequence would do."""
    ext = _validate(fseq, options)

    numbers = [int(frame) for frame in fseq.frames]
    sources = list(fseq)
    shift = options.offset
    if options.start is not None and numbers:
        shift = options.start - min(numbers)
    if numbers and min(numbers) + shift < 0:
        raise ValueError("frame numbers below 0 are not supported")

    pad = fseq.pad if options.pad is None else options.pad
    directory = fseq.path if options.dest is None else options.dest
    base = fseq.name if options.name is None else options.name
    pairs: list[_Pair] = []
    problems: list[str] = []
    for src, number in zip(sources, numbers, strict=True):
        dst = _file_name(directory, base, number + shift, pad, ext)
        if _key(src) != _key(dst):
            pairs.append((src, dst))
        elif kind == "copy":
            problems.append(f"source and destination are the same: {src}")

    if directory and not options.parents and not os.path.isdir(directory):
        problems.append(f"destination directory does not exist: {directory}")

    stats = _stat_sources(kind, pairs, problems)
    dependencies, preexisting = _check_destinations(
        kind, pairs, stats, options.overwrite, problems
    )
    ordered = _order(pairs, dependencies, problems)

    result = sequences.FileSequence(
        frames=[number + shift for number in numbers], ext=ext, pad=pad
    )
    result.path = directory or None
    result.name = base
    context = _Context(options, frozenset(preexisting))
    return Plan(kind, ordered, problems, result, context)


def _validate(fseq: sequences.FileSequence, options: _Options) -> str:
    """Refuse contradictory or impossible arguments; return the extension."""
    if options.start is not None and options.offset:
        raise ValueError("use either offset or start, not both")
    if options.pad is not None and options.pad < 1:
        raise ValueError("pad must be at least 1")
    if fseq.ext is None:
        raise ValueError("the file sequence has no extension")
    name = options.name or ""
    if os.sep in name or (os.altsep and os.altsep in name):
        raise ValueError("name must not contain a directory (use dest)")
    return fseq.ext


def _file_name(
    directory: str | None, base: str | None, number: int, pad: int, ext: str
) -> str:
    """The name of one file of a sequence."""
    stem = f"{base}." if base else ""
    return os.path.join(directory or "", f"{stem}{number:0{pad}d}.{ext}")


def _key(path: str) -> str:
    """A name that is the same for every spelling of the path."""
    return os.path.normcase(os.path.abspath(path))


def _alias(path: str) -> str:
    """A name that is the same for names that a case-blind filesystem merges."""
    return unicodedata.normalize("NFC", _key(path)).casefold()


def _same_file(info: os.stat_result, other: os.stat_result | None) -> bool:
    """Whether two stat results are for one file (same device and inode)."""
    return (
        other is not None
        and bool(info.st_ino)
        and (info.st_dev, info.st_ino) == (other.st_dev, other.st_ino)
    )


def _source_at(
    dst: str,
    info: os.stat_result,
    by_key: dict[str, int],
    by_alias: dict[str, int],
    stats: Sequence[os.stat_result | None],
) -> int | None:
    """
    The pair whose source is what is at the destination (None: unrelated).

    A hard link of a source somewhere else is an unrelated file. Only a name
    that a case-insensitive filesystem merges with the source's name, and that
    really is the same file, counts as the source itself.
    """
    index = by_key.get(_key(dst))
    if index is None:
        candidate = by_alias.get(_alias(dst))
        if candidate is not None and _same_file(info, stats[candidate]):
            index = candidate
    return index


def _stat_sources(
    kind: _Kind, pairs: Sequence[_Pair], problems: list[str]
) -> list[os.stat_result | None]:
    """Stat every source, reporting the ones that are not usable files."""
    stats: list[os.stat_result | None] = []
    for src, _ in pairs:
        try:
            # A copy reads through symlinks; a move renames the link itself.
            info = os.stat(src) if kind == "copy" else os.lstat(src)
        except FileNotFoundError:
            problems.append(f"source does not exist: {src}")
            stats.append(None)
            continue
        except OSError as error:
            problems.append(f"cannot read {src}: {error.strerror}")
            stats.append(None)
            continue
        is_file = stat.S_ISREG(info.st_mode)
        if not is_file and not (kind == "move" and stat.S_ISLNK(info.st_mode)):
            problems.append(f"not a file: {src}")
        stats.append(info)
    return stats


def _check_destinations(
    kind: _Kind,
    pairs: Sequence[_Pair],
    stats: Sequence[os.stat_result | None],
    overwrite: bool,
    problems: list[str],
) -> tuple[dict[int, set[int]], set[str]]:
    """
    Check what is already at the destinations.

    Returns:
        Which pairs must wait for which (a destination that is another pair's
        source), and the existing files that would be replaced.
    """
    by_key = {_key(src): i for i, (src, _) in enumerate(pairs)}
    by_alias = {_alias(src): i for i, (src, _) in enumerate(pairs)}

    dependencies: dict[int, set[int]] = {}
    preexisting: set[str] = set()
    written: set[str] = set()
    for i, (_, dst) in enumerate(pairs):
        if _key(dst) in written:
            problems.append(f"two files would be written to {dst}")
        written.add(_key(dst))
        try:
            info = os.lstat(dst)
        except OSError:  # nothing there (or unreadable: the transfer will say)
            continue
        if stat.S_ISDIR(info.st_mode):
            problems.append(f"destination is a directory: {dst}")
            continue
        # Is what is there one of the files we are about to move or copy?
        other = _source_at(dst, info, by_key, by_alias, stats)
        if other is None:
            preexisting.add(dst)  # an unrelated file that would be replaced
            if not overwrite:
                problems.append(f"destination exists: {dst}")
        elif other == i:
            problems.append(
                f"destination is the same file as its source (a "
                f"case-insensitive filesystem?): {dst}"
            )
        elif kind == "copy" and not overwrite:
            problems.append(
                f"destination is also a source, the copy would overwrite it: "
                f"{dst}"
            )
        else:
            dependencies.setdefault(i, set()).add(other)
            if kind == "copy":
                preexisting.add(dst)  # the overwritten source is lost
    return dependencies, preexisting


def _order(
    pairs: list[_Pair], dependencies: dict[int, set[int]], problems: list[str]
) -> list[_Pair]:
    """Order the pairs so that no source is overwritten before it is used."""
    waiting = [len(dependencies.get(i, ())) for i in range(len(pairs))]
    dependents: dict[int, list[int]] = collections.defaultdict(list)
    for i, others in dependencies.items():
        for other in others:
            dependents[other].append(i)

    ready = collections.deque(i for i, count in enumerate(waiting) if not count)
    order: list[int] = []
    while ready:
        i = ready.popleft()
        order.append(i)
        for dependent in dependents[i]:
            waiting[dependent] -= 1
            if waiting[dependent] == 0:
                ready.append(dependent)

    if len(order) < len(pairs):
        stuck = sorted(set(range(len(pairs))) - set(order))
        problems.append(
            "these files cannot be ordered safely (they would swap or "
            "rotate): " + ", ".join(pairs[i][0] for i in stuck)
        )
    return [pairs[i] for i in order]


###############################################################################
# Doing the work


def _remove(path: str) -> None:
    """Delete a file, ignoring any failure."""
    with contextlib.suppress(OSError):
        os.unlink(path)


def _make_directories(directory: str) -> list[str]:
    """Create a directory (and parents); return the new ones, deepest first."""
    new: list[str] = []
    current = os.path.abspath(directory)
    while not os.path.isdir(current):
        new.append(current)
        parent = os.path.dirname(current)
        if parent == current:  # pragma: no cover (the root always exists)
            break
        current = parent
    os.makedirs(directory, exist_ok=True)
    return new


def _remove_directories(directories: Sequence[str]) -> None:
    """Remove directories we created (deepest first), if they are empty."""
    for directory in directories:
        with contextlib.suppress(OSError):
            os.rmdir(directory)


def _copy_exclusive(src: str, dst: str, follow_symlinks: bool) -> None:
    """Copy a file to a name that must not exist yet."""
    if not follow_symlinks and os.path.islink(src):
        os.symlink(os.readlink(src), dst)  # fails if the name is taken
        return
    # Claim the name first, so a file that appeared meanwhile is never touched.
    os.close(os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666))
    try:
        shutil.copy2(src, dst)
    except OSError:
        _remove(dst)  # do not leave a partial copy behind
        raise


def _copy_file(
    src: str, dst: str, overwrite: bool, *, follow_symlinks: bool
) -> None:
    """Copy a file with its modification time."""
    if not overwrite:
        _copy_exclusive(src, dst, follow_symlinks)
        return
    # Replace atomically: the old file survives a failed copy, a symlink at the
    # destination is replaced (not written through), and so is a hard link.
    temporary = f"{dst}.{os.urandom(4).hex()}.tmp"
    _copy_exclusive(src, temporary, follow_symlinks)
    try:
        os.replace(temporary, dst)
    except OSError:
        _remove(temporary)
        raise


def _rename_exclusive(src: str, dst: str) -> None:
    """
    Rename a file, never replacing an existing destination.

    POSIX rename silently replaces, so the file is hard-linked to its new name
    first (which fails if the name is taken) and the old name removed. Where
    hard links are not available a plain rename is the best that can be done.
    """
    if os.name == "nt":  # rename refuses to replace on Windows already
        os.rename(src, dst)
        return
    try:
        os.link(src, dst, follow_symlinks=False)
    except FileExistsError:
        raise
    except (NotImplementedError, OSError) as error:
        if isinstance(error, OSError) and error.errno == errno.EXDEV:
            raise
        os.rename(src, dst)
        return
    try:
        os.unlink(src)
    except OSError:
        _remove(dst)
        raise


def _move_file(src: str, dst: str, overwrite: bool) -> None:
    """Rename a file, copying it first when it crosses filesystems."""
    try:
        if overwrite:
            os.replace(src, dst)
        else:
            _rename_exclusive(src, dst)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        _copy_file(src, dst, overwrite, follow_symlinks=False)
        os.unlink(src)  # only after the copy succeeded
