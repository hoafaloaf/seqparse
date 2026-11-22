"""The main engine for the seqparse module."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator
from operator import attrgetter
import os
from typing import Any, Literal, overload, TypedDict, TypeGuard

from seqparse.containers import FileSequenceContainer, SingletonContainer
from seqparse.files import File
from seqparse.regex import SeqparseRegexMixin
from seqparse.sequences import FileSequence, FrameSequence

__all__ = ("Seqparse",)

PathLike = str | os.DirEntry[str]


class Location(TypedDict):
    """Everything tracked in one directory."""

    seqs: defaultdict[str, FileSequenceContainer]
    files: SingletonContainer


class ScanOptions(TypedDict):
    """Options used while scanning disk for files."""

    all: bool
    stat: bool


def _new_location() -> Location:
    """An empty Location (the default for Seqparse.locations)."""
    return {
        "seqs": defaultdict(FileSequenceContainer),
        "files": SingletonContainer(),
    }


def _is_dir_entry(item: object) -> TypeGuard[os.DirEntry[str]]:
    """Whether item is a DirEntry (by name, so look-alikes work too)."""
    return type(item).__name__ == "DirEntry"


def _split_posix(path: str) -> tuple[str, str]:
    """os.path.split for POSIX paths, without its per-call overhead."""
    cut = path.rfind("/") + 1
    head, tail = path[:cut], path[cut:]
    if head and head != "/" * len(head):
        head = head.rstrip("/")
    return head, tail


def _split_native(path: str) -> tuple[str, str]:
    """
    os.path.split, with alternate separators made primary first.

    On Windows "C:/a/b" and "C:\\a\\b" then name the same directory (and
    so share one entry in Seqparse.locations).
    """
    if os.altsep:
        path = path.replace(os.altsep, os.sep)
    return os.path.split(path)


_split = _split_posix if os.sep == "/" and not os.altsep else _split_native


def _strip_trailing_sep(path: str) -> str:
    """
    Remove trailing separators, keeping roots ("/", "C:\\", UNC shares).

    Args:
        path (str): The path to clean up.

    Returns:
        str path without trailing separators, unless it is a root.
    """
    drive, rest = os.path.splitdrive(path)
    stripped = rest.rstrip(os.sep + (os.altsep or ""))
    return drive + (stripped or rest)


def _dir_key(path: str) -> tuple[int, int] | str:
    """
    Identity of a directory, for spotting symlink loops.

    (device, inode) costs one stat call, where os.path.realpath costs one per
    path component. Paths that can't be stat'd (os.scandir will report
    those) and filesystems without inode numbers fall back to realpath.
    """
    try:
        info = os.stat(path)
    except OSError:
        return os.path.realpath(path)
    if info.st_ino:
        return (info.st_dev, info.st_ino)
    return os.path.realpath(path)  # pragma: no cover


def _is_ancestor(path: str, parents: Iterable[str]) -> bool:
    """Whether path resolves to the same directory as one of parents."""
    real = os.path.realpath(path)
    return any(os.path.realpath(parent) == real for parent in parents)


def _stat(
    file_name: str, entry: os.DirEntry[str] | None = None
) -> os.stat_result:
    """
    Disk stats for a file, following symlinks.

    Args:
        file_name (str): Path to the file.
        entry (DirEntry, optional): The file's DirEntry when it was found via
            scan_path; its cached stat is used in preference to os.stat.

    Returns:
        stat_result for the file.
    """
    if entry:
        return entry.stat(follow_symlinks=True)
    return os.stat(file_name)


###############################################################################
# Class: Seqparse


class Seqparse(SeqparseRegexMixin):
    """
    Storage and parsing engine for file sequences.

    The primary usage for this class is to scan specified locations on disk for
    file sequences and singletons (any file that cannot be classified as a
    member of a file sequence).

    Examples:

        With the following file structure ...

            test_dir/
                TEST_DIR.0001.tif
                TEST_DIR.0002.tif
                TEST_DIR.0003.tif
                TEST_DIR.0004.tif
                TEST_DIR.0010.tif
                SINGLETON.jpg

        >>> from seqparse.seqparse import Seqparse
        >>> parser = Seqparse()
        >>> parser.scan_path("test_dir")
        >>> for item in parser.output():
        ...     print str(item)
        ...
        test_dir/TEST_DIR.0001-0004,0010.tif
        test_dir/SINGLETON.jpg
        >>> for item in parser.output(seqs_only=True):
        ...     print str(item)
        ...
        test_dir/TEST_DIR.0001-0004,0010.tif
        >>> for item in parser.output(missing=True):
        ...     print str(item)
        ...
        test_dir/TEST_DIR.0005-0009.tif
    """

    def __init__(self) -> None:
        """Initialise the instance."""
        super().__init__()

        self._locs: defaultdict[str, Location] = defaultdict(_new_location)
        self._options: ScanOptions = {"all": False, "stat": False}

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        num_seqs = sum(1 for _ in self.output(seqs_only=True))
        num_files = sum(1 for _ in self.output()) - num_seqs
        return (
            f"{type(self).__name__}(sequences={num_seqs}, "
            f"singletons={num_files})"
        )

    @property
    def locations(self) -> defaultdict[str, Location]:
        """A dictionary of tracked singletons and file sequences."""
        return self._locs

    @property
    def scan_options(self) -> ScanOptions:
        """A dictionary of options used while scanning disk for files."""
        return self._options

    @property
    def sequences(self) -> dict[str, defaultdict[str, FileSequenceContainer]]:
        """A dictionary of tracked file sequences."""
        return self._get_data("seqs")

    @property
    def singletons(self) -> dict[str, SingletonContainer]:
        """A dictionary of tracked singleton files."""
        return self._get_data("files")

    def add_file(self, file_name: PathLike) -> None:
        """
        Add a file to the parser instance.

        Args:
            file_name (str): The name of the file you'd like to add to the
                parser.

        Returns:
            None
        """
        if _is_dir_entry(file_name):
            self._add_path(file_name.path, True, file_name)
        else:
            self._add_path(str(file_name), False, None)

    def _add_file(self, file_name: PathLike, on_disk: bool = False) -> None:
        """
        Add a file (or, for strings, a whole file sequence) to the instance.

        Args:
            file_name (str or DirEntry): The file to add.
            on_disk (bool, optional): Whether file_name is a single file that
                exists on disk (a DirEntry or a path found by scanning).

        Returns:
            None
        """
        if _is_dir_entry(file_name):
            self._add_path(file_name.path, on_disk, file_name)
        else:
            self._add_path(str(file_name), on_disk, None)

    def _add_path(
        self, path: str, on_disk: bool, entry: os.DirEntry[str] | None
    ) -> None:
        """
        Add a file (or a whole file sequence) by name; see _add_file.

        Args:
            path (str): The file (or file sequence) name.
            on_disk (bool): Whether path is a single file that exists on disk.
            entry (DirEntry or None): The file's DirEntry, if it has one.

        Returns:
            None
        """
        dir_name, base_name = _split(path)

        # A file found on disk is a single frame; a frame *sequence* in its
        # name (eg "foo.1-3.exr") is just part of a singleton's name. Strings
        # passed in directly may describe a whole sequence of files.
        match = (self._file_expr if on_disk else self._fseq_expr).match(
            base_name
        )

        if match:
            seq_name, frames, ext_name = match.groups()
            seq_name = seq_name or ""

            loc = self.locations[dir_name]
            sequence = loc["seqs"][seq_name]

            # Set the name and path properties at initialization.
            if not sequence:
                sequence.name = seq_name
                sequence.path = dir_name

            # We'll assume that a frame sequence is properly formed -- and use
            # the length of the first frame as the padding. The FrameSequence
            # to which we're adding the frames will do the actual validation.
            if frames.isdecimal():
                pad = len(frames)
            else:
                first_chunk = frames.lstrip(",").split(",")[0]
                pad = len(first_chunk.partition("-")[0])

            ext = sequence[ext_name]
            ext[pad].add(frames)

            # Disk stats only make sense for a single file (frame).
            if self.scan_options["stat"] and frames.isdigit():
                ext[pad].cache_stat(int(frames), _stat(path, entry))

        else:
            loc = self.locations[dir_name]

            singletons = loc["files"]

            # Set the path properties at initialization.
            if not singletons:
                singletons.path = dir_name

            singletons.add(base_name)
            if self.scan_options["stat"]:
                singletons.cache_stat(base_name, _stat(path, entry))

    @overload
    def output(
        self, missing: Literal[True], seqs_only: bool = ...
    ) -> Iterator[FileSequence]: ...
    @overload
    def output(
        self, missing: bool = ..., *, seqs_only: Literal[True]
    ) -> Iterator[FileSequence]: ...
    @overload
    def output(
        self, missing: bool = False, seqs_only: bool = False
    ) -> Iterator[File | FileSequence]: ...
    def output(
        self, missing: bool = False, seqs_only: bool = False
    ) -> Iterator[File | FileSequence]:
        """
        Yield a list of contained singletons and file sequences.

        Args:
            missing (bool, optional): Whether to yield "inverted" file
                sequences (ie, the missing files). Defaults to False. NOTE:
                Using this option implies that seqs_only == True.
            seqs_only (bool, optional): Whether to only yield file sequences
                (if any). Defaults to False.

        Yields:
            File and/or FileSequence instances, depending on input arguments.
        """
        if missing:
            seqs_only = True

        for root_dir in sorted(self.locations):
            data = self.locations[root_dir]
            for container in sorted(
                data["seqs"].values(), key=attrgetter("full_name")
            ):
                for file_seq in container.output():
                    if not missing:
                        yield file_seq
                        continue
                    inverted = file_seq.invert()
                    # No gaps: nothing is missing.
                    if inverted:
                        yield inverted

            if seqs_only:
                continue

            # output() already yields the files sorted by name.
            yield from data["files"].output()

    def scan_path(
        self,
        search_paths: str | list[str] | set[str] | tuple[str, ...],
        max_levels: int = -1,
        min_levels: int = -1,
    ) -> None:
        """
        Scan supplied path, add all discovered files to the instance.

        Args:
            search_paths (str): The location(s) on disk you'd like to scan for
                file sequences and singletons.
            max_levels (int, optional): Descend at most the specified number (a
                non- negative integer) of directories below the starting point.
                max_levels == 0 means only scan the starting-point itself.
            min_levels (int, optional): Do not scan at levels less than
                specified number (a non-negative integer). min_levels == 1
                means scan all levels except the starting-point.

        Returns:
            None
        """
        if isinstance(search_paths, (list, set, tuple)):
            for search_path in search_paths:
                self.scan_path(
                    search_path, max_levels=max_levels, min_levels=min_levels
                )
            return
        if os.path.isfile(search_paths):
            # Treat it exactly as a directory scan would treat the same file.
            self._add_file(search_paths, on_disk=True)
            return

        search_path = _strip_trailing_sep(search_paths)

        for cur_level, dir_entries, file_entries in self._scandir_walk(
            search_path
        ):
            max_out = max_levels > -1 and cur_level >= max_levels
            min_out = min_levels > -1 and cur_level < min_levels

            if max_out:
                del dir_entries[:]
            if min_out:
                del file_entries[:]

            self._add_from_scan(file_entries)

    def _add_from_scan(self, file_entries: Iterable[os.DirEntry[str]]) -> None:
        """
        Shortcut for adding file sequences from os/scandir.walk.

        Args:
            file_entries (iterable): Iterable (list-like object or generator)
                of scandir-style DirEntry instances for files discovered on
                disk.

        Returns:
            None
        """
        for file_entry in file_entries:
            self.add_file(file_entry)

    @overload
    def _get_data(
        self, typ: Literal["seqs"]
    ) -> dict[str, defaultdict[str, FileSequenceContainer]]: ...
    @overload
    def _get_data(
        self, typ: Literal["files"]
    ) -> dict[str, SingletonContainer]: ...
    def _get_data(
        self, typ: Literal["seqs", "files"]
    ) -> (
        dict[str, defaultdict[str, FileSequenceContainer]]
        | dict[str, SingletonContainer]
    ):
        """
        Return dictionary of the specified data type from the instance.

        Args:
            typ (str): "seqs" (for file sequences) or "files" (for singletons).

        Returns:
            dict of all data of the specified type, indexed by containing
            directory.
        """
        output: dict[str, Any] = {}
        for loc, data in self.locations.items():
            if data[typ]:
                output[loc] = data[typ]
        return output

    def _scandir_walk(
        self,
        search_path: str,
        follow_symlinks: bool = True,
        _level: int = 0,
        _ancestors: frozenset[tuple[int, int] | str] = frozenset(),
        _parents: tuple[str, ...] = (),
    ) -> Iterator[tuple[int, list[os.DirEntry[str]], list[os.DirEntry[str]]]]:
        """
        Recursively yield DirEntry objects for given directory.

        A directory that resolves to one of its own ancestors (a symlink loop)
        is skipped, as are subdirectories that cannot be read. Other symlinked
        directories are followed, so their files are reported under every path
        that reaches them (like `find -L`).

        Args:
            search_path (str): Directory to scan for files.
            follow_symlinks (bool, optional): Whether to follow symlinks
                dicovered at scan time. Defaults to True.

        Yields:
            tuple of (depth below the starting point, list of directory
            DirEntry instances, list of file DirEntry instances). Removing
            items from the directory list prevents descending into them.
        """
        key = _dir_key(search_path)
        # Some network/FUSE filesystems reuse inode numbers: confirm a match
        # by path before treating it as a symlink loop.
        if key in _ancestors and _is_ancestor(search_path, _parents):
            return
        _ancestors = _ancestors | {key}

        dir_entries: list[os.DirEntry[str]] = []
        file_entries: list[os.DirEntry[str]] = []
        try:
            entries = list(os.scandir(search_path))
        except OSError:
            # Let errors on the starting point propagate to the caller.
            if not _level:
                raise
            return

        for entry in entries:
            if entry.name.startswith(".") and not self.scan_options["all"]:
                continue
            if entry.is_dir(follow_symlinks=follow_symlinks):
                dir_entries.append(entry)
            elif entry.is_file(follow_symlinks=follow_symlinks):
                file_entries.append(entry)

        yield _level, dir_entries, file_entries

        for entry in dir_entries:
            yield from self._scandir_walk(
                entry.path,
                follow_symlinks=follow_symlinks,
                _level=_level + 1,
                _ancestors=_ancestors,
                _parents=(*_parents, search_path),
            )

    @staticmethod
    def validate_frame_sequence(frame_seq: str) -> str | None:
        """
        Whether the supplied frame (not file) sequence is valid.

        Args:
            frame_seq (str): The string representation of the frame sequence
                to validate.

        Returns:
            None if the supplied sequence is invalid, a (possibly corrected)
            string file sequence if valid.

        Examples:
            >>> from seqparse.seqparse import Seqparse
            >>> parser = Seqparse()
            >>> print parser.validate_frame_sequence("0001-0001")
            0001
            >>> print parser.validate_frame_sequence("0001-")
            None
            >>> print parser.validate_frame_sequence("3,1,5,7")
            1-7x2
        """
        try:
            seq = FrameSequence(frame_seq)
        except ValueError:
            return None

        return str(seq)
