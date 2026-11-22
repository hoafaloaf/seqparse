"""Classes utilized by the Seqparse class."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, MutableMapping, MutableSet
import functools
import itertools
import operator
import os
from typing import Any, Final, overload, TypeVar

import seqparse
from seqparse import files, sequences

__all__ = ("FileExtension", "FileSequenceContainer", "SingletonContainer")

# Sentinel for "no default given" (None is a valid default for pop()).
_MISSING: Final = object()

_K = TypeVar("_K")
_V = TypeVar("_V")
_T = TypeVar("_T")


###############################################################################
# Class: _AutoMapping


class _AutoMapping(MutableMapping[_K, _V]):
    """
    Mapping that creates missing entries when indexed, like defaultdict.

    Unlike MutableMapping's defaults, `in`, get(), pop() and setdefault() look
    at the stored entries directly and never create one as a side effect.
    Subclasses implement _create() and __setitem__().
    """

    def __init__(self) -> None:
        """Initialise the instance."""
        self._data: dict[_K, _V] = {}

    def _create(self, key: _K) -> _V:
        """Create the entry for a missing key."""
        raise NotImplementedError

    def __getitem__(self, key: _K) -> _V:
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self._data:
            self._data[key] = self._create(key)
        return self._data[key]

    def __delitem__(self, key: _K) -> None:
        """Define key deletion logic (per standard dictionary)."""
        del self._data[key]

    def __contains__(self, key: object) -> bool:
        """Membership test that, like defaultdict, never creates entries."""
        return key in self._data

    def __iter__(self) -> Iterator[_K]:
        """Define key iteration logic (per standard dictionary)."""
        return iter(self._data)

    def __len__(self) -> int:
        """Define item length logic (per standard dictionary)."""
        return len(self._data)

    @overload
    def get(self, key: _K) -> _V | None: ...
    @overload
    def get(self, key: _K, default: _V | _T) -> _V | _T: ...
    def get(self, key: _K, default: object = None) -> object:
        """Look up a key without creating it (per collections.defaultdict)."""
        return self._data.get(key, default)

    @overload
    def pop(self, key: _K) -> _V: ...
    @overload
    def pop(self, key: _K, default: _V) -> _V: ...
    @overload
    def pop(self, key: _K, default: _T) -> _V | _T: ...
    def pop(self, key: _K, default: object = _MISSING) -> object:
        """Remove and return a key's value without creating missing keys."""
        if default is _MISSING:
            return self._data.pop(key)
        return self._data.pop(key, default)

    def setdefault(self, key: _K, default: Any = None) -> _V:
        """
        Return a key's value, inserting `default` if the key is missing.

        With no default, a missing key gets a new empty child (like indexing,
        per collections.defaultdict).
        """
        if key not in self._data:
            if default is None:
                return self[key]
            self[key] = default
        return self._data[key]


###############################################################################
# Class: FileExtension


class FileExtension(_AutoMapping[int, sequences.FileSequence]):
    """
    Container for frame sequences, indexed by zero-padding.

    Args:
        name (str, optional): The file extension used by the contents of the
            container (ie, "exr", "tif").
        parent (FileSequenceContainer, optional): The container from which this
            instance was spawned.
    """

    _CHILD_CLASS = sequences.FileSequence

    def __init__(
        self,
        name: str | None = None,
        parent: FileSequenceContainer | None = None,
    ) -> None:
        """Initialise the instance."""
        super().__init__()
        self._name: str | None = None
        self._parent: FileSequenceContainer | None = None

        self.name = name
        self.parent = parent

    def _create(self, key: int) -> sequences.FileSequence:
        """Create an empty sequence for a missing pad."""
        return self._adopt(self._CHILD_CLASS(ext=self.name, pad=key))

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return f"{type(self).__name__}(name={self.name!r}, pads={sorted(self)})"

    def __setitem__(self, key: int, value: object) -> None:
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._adopt(
                self._CHILD_CLASS(ext=self.name, frames=value, pad=key)
            )

        if not isinstance(value, self._CHILD_CLASS):
            raise TypeError(
                f'Container may only hold "{self._CHILD_CLASS.__name__}" '
                f'instances ("{type(value).__name__}" provided)'
            )

        self._data[key] = value

    @property
    def name(self) -> str | None:
        """str: name of the file extension."""
        return self._name

    @name.setter
    def name(self, val: object) -> None:
        self._name = str(val) if val else None

    @property
    def parent(self) -> FileSequenceContainer | None:
        """FileSequenceContainer: parent of the instance."""
        return self._parent

    @parent.setter
    def parent(self, val: object) -> None:
        self._parent = None
        if isinstance(val, FileSequenceContainer):
            self._parent = val
            # Sequences added before the parent was set adopt its names too.
            for child in self._data.values():
                self._adopt(child)

    def _adopt(self, child: sequences.FileSequence) -> sequences.FileSequence:
        """Give a child sequence the parent container's path and name."""
        # An empty container is falsy (it's a mapping): test identity.
        if self.parent is not None:
            child.path = self.parent.path
            child.name = self.parent.name
        return child

    def output(self) -> Iterator[sequences.FileSequence]:
        """
        Calculate a sorted list of all contained file extentions.

        Yields:
            FrameSequence, sorted by zero-pad length.
        """
        # First, check to see if we need to consolidate our file sequences.
        # Walk the pads from largest to smallest: an unpadded sequence merges
        # into the sequence with the next smaller pad.
        data = sorted(
            self._data.items(), key=operator.itemgetter(0), reverse=True
        )
        for (pad, fseq), (_, next_fseq) in itertools.pairwise(data):
            # NOTE: the is_padded() method will force recalculation if the
            # object is dirty.
            if not fseq.is_padded:
                next_fseq.update(fseq)
                del self[pad]

        for pad in sorted(self):
            yield self[pad]


###############################################################################
# Class: FileSequenceContainer


@functools.total_ordering
class FileSequenceContainer(_AutoMapping[str, FileExtension]):
    """
    Container for file sequences, indexed by file extension.

    Args:
        name (str, optional): Base name of the contained files.
        file_path (str, optional): Directory in which the contained files
            reside.
    """

    _CHILD_CLASS = FileExtension

    # Mutable, and equality depends on mutable state: deliberately
    # unhashable (like set and dict).
    __hash__ = None  # type: ignore[assignment]

    def __init__(
        self, name: str | None = None, file_path: str | None = None
    ) -> None:
        """Initialise the instance."""
        super().__init__()
        self._full = ""
        self._name: str | None = None
        self._path: str | None = None

        self.name = name
        self.path = file_path

    def _create(self, key: str) -> FileExtension:
        """Create an empty extension container for a missing extension."""
        return self._CHILD_CLASS(name=key, parent=self)

    def __eq__(self, other: object) -> bool:
        """
        Define equality between instances.

        NOTE: Equality is solely based upon comparison of the "full_name"
        property and is only used for output sorting.
        """
        if isinstance(other, FileSequenceContainer) and type(other) is type(
            self
        ):
            return self.full_name == other.full_name
        return False

    def __lt__(self, other: object) -> bool:
        """
        Define whether one instance may be sorted below another.

        NOTE: Equality is solely based upon comparison of the "full_name"
        property and is only used for output sorting.
        """
        if isinstance(other, FileSequenceContainer) and type(other) is type(
            self
        ):
            return self.full_name < other.full_name
        return True

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return (
            f"{type(self).__name__}(full_name={self.full_name!r}, "
            f"exts={sorted(self)})"
        )

    def __setitem__(self, key: str, value: object) -> None:
        """Define item setting logic (per standard dictionary)."""
        if not isinstance(value, self._CHILD_CLASS):
            raise TypeError(
                f'Container may only hold "{self._CHILD_CLASS.__name__}" '
                f'instances ("{type(value).__name__}" provided)'
            )

        if key != value.name:
            raise ValueError(
                "Key value must match extension name of provided value "
                f"({key!r} != {value.name!r})"
            )

        self._data[key] = value
        value.parent = self

    @property
    def full_name(self) -> str:
        """str: Full (base) name of the file sequence."""
        return self._full

    @property
    def name(self) -> str | None:
        """str: Base name of the file sequence (no containing directory)."""
        return self._name

    @name.setter
    def name(self, val: object) -> None:
        self._name = str(val) if val else None
        self._full = os.path.join(self._path or "", self._name or "")

    @property
    def path(self) -> str | None:
        """str: directory in which the contained files reside."""
        return self._path

    @path.setter
    def path(self, val: object) -> None:
        self._path = str(val) if val else None
        self._full = os.path.join(self._path or "", self._name or "")

    def output(self) -> Iterator[sequences.FileSequence]:
        """
        Calculate a sorted list of all contained file sequences.

        Yields:
            FileSequence, sorted (in order) by file path, extension, and zero-
                padding length.
        """
        for ext in sorted(self):
            yield from self[ext].output()


###############################################################################
# class: SingletonContainer


class SingletonContainer(MutableSet[str]):
    """
    Container for singleton files, indexed alphabetically by file path.

    Args:
        file_names (list-like of str, optional): List of base file names to
            store in the container.
        file_path (str, optional): Directory in which the contained files
            reside.
    """

    def __init__(
        self,
        file_names: Iterable[object] | None = None,
        file_path: str | None = None,
    ) -> None:
        """Initialise the instance."""
        self._data: set[str] = set()
        self._path = ""
        self._stat: dict[str, os.stat_result] = {}

        for item in file_names or []:
            self.add(item)

        self.path = file_path

    def __contains__(self, item: object) -> bool:
        """Defining containment logic (per standard set)."""
        return str(item) in self._data

    def __iter__(self) -> Iterator[str]:
        """Defining item iteration logic (per standard set)."""
        return iter(self._data)

    def __len__(self) -> int:
        """Defining item length logic (per standard set)."""
        return len(self._data)

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return (
            f"{type(self).__name__}(path='{self.path}', "
            f"files=set({sorted(self._data)}))"
        )

    def __str__(self) -> str:
        """String reprentation of the singleton files."""
        return "\n".join(map(str, self.output()))

    @property
    def path(self) -> str:
        """Directory in which the contained files are located."""
        return self._path

    @path.setter
    def path(self, val: object) -> None:
        self._path = str(val or "")

    def add(self, value: object) -> None:
        """Defining item addition logic (per standard set)."""
        self._data.add(str(value))

    def discard(self, value: object) -> None:
        """Defining item discard logic (per standard set)."""
        value = str(value)
        self._data.discard(value)
        self._stat.pop(value, None)

    def update(self, iterable: Iterable[object]) -> None:
        """Defining update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def cache_stat(
        self, base_name: str, input_stat: seqparse.StatLike
    ) -> os.stat_result:
        """
        Cache file system stat data for the specified file base name.

        Input disk stat value will be stored in a new stat_result
        instance.

        Args:
            base_name (str): Base name of the file for which the supplied disk
                stats are being cached.
            input_stat (stat_result): Value that you'd like to cache.

        Returns:
            stat_result that was successfully cached.
        """
        self._stat[base_name] = seqparse.get_stat_result(input_stat)
        return self._stat[base_name]

    def output(self) -> Iterator[files.File]:
        """
        Calculate formatted list of all contained file sequences.

        Yields:
            File, sorted alphabetically.
        """
        for file_name in sorted(self):
            yield files.File(
                os.path.join(self.path, file_name), self.stat(file_name)
            )

    @overload
    def stat(self) -> dict[str, os.stat_result]: ...
    @overload
    def stat(self, base_name: str) -> os.stat_result | None: ...
    def stat(
        self, base_name: str | None = None
    ) -> dict[str, os.stat_result] | os.stat_result | None:
        """
        Individual file system status, indexed by base name.

        This method only returns cached disk stats (if any exist). Use the
        `cache_stat` method if you'd like to set new values.

        Args:
            base_name (str, optional): Base name of the file for which you'd
                like to return the disk stats.

        Returns:
            None if a file has been specified but disk stats have not been
            cached.
            stat_result if a file has been specified and disk stats have
            been previously cached.
            dict of disk stats, indexed by str base name if no name has been
            specified.
        """
        if base_name is None:
            return self._stat
        return self._stat.get(base_name, None)
