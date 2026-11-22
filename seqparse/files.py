"""Singleton file-related data structures utilized by the Seqparse module."""

from __future__ import annotations

from functools import total_ordering
import os
from typing import Any

from seqparse import get_stat_result, restore_slots, StatLike

__all__ = ("File",)

###############################################################################
# Class: File


@total_ordering
class File:
    """
    Simple representation of files on disk.

    Args:
        file_name (str): Full path to the input file.
        stat (stat_result, optional): Disk stats you'd like to cache for the
            specified file.
    """

    # __dict__ and __weakref__ keep custom attributes and weak references
    # working (the dict is only created if used).
    __slots__ = ("__dict__", "__weakref__", "_full", "_name", "_path", "_stat")

    _full: str
    _name: str
    _path: str
    _stat: os.stat_result | None

    def __init__(self, file_name: str, stat: StatLike | None = None) -> None:
        """Initialise the instance."""
        self._stat = None
        self._cache_stat(stat)
        self._set_name(file_name)

    def __setstate__(self, state: Any) -> None:
        """Unpickle, including pickles made by seqparse 1.0.x."""
        if isinstance(state, tuple):
            restore_slots(self, state)
            return
        info = state["_info"]  # 1.0.x kept its state in plain dicts
        self._full, self._name, self._path = (
            info["full"],
            info["name"],
            info["path"],
        )
        self._stat = state["_stat"]

    def __eq__(self, other: object) -> bool:
        """Define equality between instances."""
        if type(other) is type(self):
            assert isinstance(other, File)
            return self.full_name == other.full_name
        return False

    def __hash__(self) -> int:
        """Hash consistently with __eq__ (the name is fixed at creation)."""
        return hash((type(self), self.full_name))

    def __lt__(self, other: object) -> bool:
        """Define equality between instances."""
        if type(other) is type(self):
            assert isinstance(other, File)
            return self.full_name < other.full_name
        return True

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return f"{type(self).__name__}({self._full!r})"

    def __str__(self) -> str:
        """String representation of a File instance."""
        return str(self.full_name)

    @property
    def full_name(self) -> str:
        """str: Full name of the sequence, including containing directory."""
        return self._full

    @property
    def mtime(self) -> float | None:
        """
        int: Modification time of the file.

        Returns None if the files have not been stat'd on disk.
        """
        if not self._stat:
            return None
        return self._stat.st_mtime

    @property
    def name(self) -> str:
        """str: Base name of the file sequence (no containing directory)."""
        return self._name

    @property
    def path(self) -> str:
        """str: Directory in which the contained files are located."""
        return self._path

    @property
    def size(self) -> int | None:
        """
        int: Size of the file in bytes.

        Returns None if the files have not been stat'd on disk.
        """
        if not self._stat:
            return None
        return self._stat.st_size

    def _cache_stat(self, input_stat: StatLike | None) -> os.stat_result | None:
        """
        Cache file system stat data.

        Args:
            input_stat (stat_result): Value that you'd like to cache.

        Returns:
            stat_result that was successfully cached.
        """
        self._stat = None
        if input_stat:
            self._stat = get_stat_result(input_stat)
        return self._stat

    def _set_name(self, full_name: str) -> None:
        """
        Set all name-related fields on the instance.

        Args:
            full_name (str): Full path to the contained file.
        """
        self._path, self._name = os.path.split(full_name)
        self._full = full_name

    def stat(
        self, force: bool = False, lazy: bool = False
    ) -> os.stat_result | None:
        """
        File system status.

        Args:
            force (bool, optional): Whether to force disk stat query,
                regardless of caching status.
            lazy (bool, optional): Whether to query disk stats should no cached
                value exist.

        Returns:
            None if a frame has been specified but disk stats have not been
            cached.
            stat_result if a frame has been specified and disk stats have
            been previously cached.
        """
        if force or (lazy and self._stat is None):
            self._cache_stat(os.stat(self.full_name))
        return self._stat
