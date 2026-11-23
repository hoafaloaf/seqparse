"""Sequence-related data structures utilized by the Seqparse module."""

from __future__ import annotations

import array
import bisect
from collections.abc import Iterable, Iterator, MutableSequence, MutableSet
import itertools
import operator
import os
from typing import Any, overload, SupportsInt, TypeAlias

import seqparse
from seqparse import regex

__all__ = ("FileSequence", "FrameChunk", "FrameSequence", "SeqparsePadError")

# Anything a FrameSequence accepts as frames: a frame number (int or digit
# string), a frame sequence string, a FrameChunk/FrameSequence, or an iterable
# of frames.
Frames: TypeAlias = str | SupportsInt | Iterable[Any]


def _is_iterable(value: object) -> bool:
    """Whether value is a non-string iterable (list, set, range, ...)."""
    if isinstance(value, (str, bytes)):
        return False
    try:
        iter(value)  # type: ignore[call-overload]
    except TypeError:
        return False
    return True


def _frame_number(item: Any) -> int:
    """The integer frame number of item (raises like int() on bad input)."""
    return int(item)


def _contained_frame(item: Any) -> int | None:
    """The frame a membership test asks about; None for 1.5 (not a frame)."""
    number = _frame_number(item)
    return number if isinstance(item, str) or number == item else None


# Frames are stored as a sorted array of 64-bit ints (8 bytes per frame, no
# int objects); frame numbers too big for that fall back to a list.
FrameStore: TypeAlias = MutableSequence[int]

# Up to this many pending frames are merged by binary-search insertion;
# more are merged by a full sort.
_SMALL_MERGE = 32


def _compact(values: list[int]) -> FrameStore:
    """Store sorted, unique frames as compactly as their size allows."""
    try:
        return array.array("q", values)
    except OverflowError:
        return values


def _exact_frame(value: object) -> int | None:
    """value as a frame number if it is exactly one (1.0 is; 1.5 isn't)."""
    try:
        number = _frame_number(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if number == value else None


def _is_correctly_padded(value: str, pad: int) -> bool:
    """
    Whether a string frame is correctly zero-padded for the given padding.

    A frame with leading zeros must be exactly `pad` digits long; a frame with
    no leading zeros may be as long as (or longer than) `pad`.
    """
    if value.startswith("0"):
        return len(value) == pad
    return len(value) >= pad


###############################################################################
# Class: SeqparsePadError


class SeqparsePadError(ValueError):
    """
    Exception thrown when unexpected frame padding is encountered.

    Subclasses ValueError: incorrect padding is an invalid value, and callers
    catching ValueError for bad frame input should catch this too.
    """


###############################################################################
# Class: FrameChunk


class FrameChunk:
    """
    Representative for chunks of frames in a FrameSequence.

    Args:
        first (int): First frame of the chunk.
        last (int, optional): Last frame of the chunk. Defaults to first
            frame if not specified.
        step (int, optional): Step size for the chunk. Defaults to 1.
        pad (int, optional): Frame padding for the chunk. Defaults to 1.
    """

    # __dict__ and __weakref__ keep custom attributes and weak references
    # working (the dict is only created if used).
    __slots__ = (
        "__dict__",
        "__weakref__",
        "_first",
        "_last",
        "_length",
        "_output",
        "_pad",
        "_step",
    )

    _first: int
    _last: int
    _length: int
    _output: str
    _pad: int
    _step: int

    # Mutable, and equality depends on mutable state: deliberately
    # unhashable (like set and dict).
    __hash__ = None  # type: ignore[assignment]

    def __init__(
        self,
        first: SupportsInt | str,
        last: SupportsInt | str | None = None,
        step: SupportsInt | str | None = 1,
        pad: SupportsInt | str = 1,
    ) -> None:
        """Initialise the instance."""
        self._pad = int(pad)
        # This will calculate the string output as well!
        self.set_frames(first, last, step)

    def __setstate__(self, state: Any) -> None:
        """Unpickle, including pickles made by seqparse 1.0.x."""
        if isinstance(state, tuple):
            seqparse.restore_slots(self, state)
            return
        data = state["_data"]  # 1.0.x kept its state in plain dicts
        self._first, self._last = data["first"], data["last"]
        self._length, self._pad, self._step = (
            data["length"],
            data["pad"],
            data["step"],
        )
        self._output = state["_output"]

    def __contains__(self, item: object) -> bool:
        """Whether the chunk contains the specified (non-)padded frame."""
        frame_num = _contained_frame(item)
        if frame_num is None or not self._first <= frame_num <= self._last:
            return False
        if (frame_num - self._first) % self.step:
            return False
        if isinstance(item, str):
            return _is_correctly_padded(item, self._pad)
        return True

    def __eq__(self, other: object) -> bool:
        """Define equality between instances."""
        if isinstance(other, FrameChunk) and type(other) is type(self):
            return self._key() == other._key()
        return False

    def __iter__(self) -> Iterator[str]:
        """Iterate over the frames contained by the chunk."""
        spec = f"0{self._pad}d"
        for frame in range(self._first, self._last + 1, self.step):
            yield format(frame, spec)

    def __len__(self) -> int:
        """Return the length of the frame chunk."""
        return self._length

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return (
            f"{type(self).__name__}(first={self._first}, last={self._last}, "
            f"step={self._step}, length={self._length}, pad={self._pad})"
        )

    def __reversed__(self) -> Iterator[str]:
        """Allow reversed iteration via reversed()."""
        spec = f"0{self._pad}d"
        for frame in reversed(range(self._first, self._last + 1, self.step)):
            yield format(frame, spec)

    def __str__(self) -> str:
        """String representation of the frame chunk."""
        return self._output

    def _key(self) -> tuple[int, int, int, int, int]:
        """Everything equality depends on."""
        return (self._first, self._last, self._length, self._pad, self._step)

    @property
    def first(self) -> int:
        """int: first frame of the chunk."""
        return self._first

    @property
    def last(self) -> int:
        """int: Last frame of the chunk."""
        return self._last

    @property
    def pad(self) -> int:
        """int: zero-padding for the frames contained by the object."""
        return self._pad

    @property
    def step(self) -> int:
        """int: step size for the frame chunk."""
        return max(self._step, 1)

    def invert(
        self, first: int | None = None, last: int | None = None
    ) -> FrameSequence:
        """
        Calculate iterator for the frames missing from the chunk.

        Args:
            first (int, optional): First frame of the range that you'd like to
                invert. Defaults to first frame of the chunk if not specified.
            last (int, optional): Last frame of the range that you'd like to
                invert. Defaults to last frame of the chunk if not specified.

        Returns:
            FrameSequence instance containing the missing frames (if any).

        Examples:
            >>> from seqparse.sequences import FrameChunk
            >>> chunk = FrameChunk(first=5, last=11, step=2, pad=3)
            >>> print(chunk)
            005-011x2
            >>> inverted = chunk.invert()
            >>> print(inverted)
            006-010x2
            >>> print(repr(inverted))
            FrameSequence(pad=3, frames=set([6, 8, 10]))
            >>> print(chunk.invert(first=1))
            001-004,006-010x2
            >>> print(chunk.invert(last=15))
            006-012x2,013-015
            >>> print(chunk.invert(first=1, last=15))
            001-004,006-012x2,013-015
        """
        if first is None:
            first = self._first
        if last is None:
            last = self._last

        missing = set(range(first, last + 1))
        missing.difference_update(range(self._first, self._last + 1, self.step))
        inverted = FrameSequence(pad=self._pad)
        inverted._frames = _compact(sorted(missing))
        return inverted

    def set_frames(
        self,
        first: SupportsInt | str,
        last: SupportsInt | str | None = None,
        step: SupportsInt | str | None = 1,
    ) -> str:
        """
        Set and validate the first and last frames of the chunk.

        Args:
            first (int): First frame of the chunk.
            last (int, optional): Last frame of the chunk. Defaults to first
                frame if not specified.
            step (int, optional): Step size for the chunk. Defaults to 1.

        Returns:
            str representation of the frame chunk.
        """
        if last is None:
            last = first

        low = int(first)
        high = int(last)
        size = max(1, int(step or 1))

        if high < low:
            raise ValueError(
                f"Last frame is less than first frame: {high:d} < {low:d}"
            )

        # Calculate the length and the real last frame of the chunk.
        bits = (high - low) // size
        high = low + bits * size
        size = min(high - low, size)

        # Calculate the string representation of the frame chunk.
        spec = f"0{self._pad}d"
        output = format(low, spec)
        if bits == 1:
            output += "," + format(high, spec)
        elif bits > 1:
            output += "-" + format(high, spec)
        if size > 1 and bits > 1:
            output += f"x{size:d}"

        self._first, self._last, self._step = low, high, size
        self._length = 1 + bits
        self._output = output
        return output


###############################################################################
# Class: FrameSequence


class FrameSequence(MutableSet[str], regex.SeqparseRegexMixin):
    """
    Representative for zero-padded frame sequences.

    Args:
        frames (many types, optional): Initial frame range to store in the
            instance. Acceptable input types include FrameChunk, FrameSequence
            instances, string representation of a frame sequence, list, set, or
            tuple of integer frames.
        pad (int, optional): Initial zero-padding for the instance. Ignored
            if input iterable is a either a FrameChunk, FrameSequence, or
            string representation of a frame sequence.

    Examples:
        All of the following will result in equivalent output:

        >>> FrameSequence(range(1, 6), pad=4)
        FrameSequence(pad=4, frames=set([1, 2, 3, 4, 5]))
        >>> FrameSequence(set([1, 2, 3, 4, 5]), pad=4)
        FrameSequence(pad=4, frames=set([1, 2, 3, 4, 5]))
        >>> FrameSequence("0001-0005")
        FrameSequence(pad=4, frames=set([1, 2, 3, 4, 5]))
        >>> FrameSequence(FrameChunk(first=1, last=5, pad=4))
        FrameSequence(pad=4, frames=set([1, 2, 3, 4, 5]))
    """

    # __dict__ and __weakref__ keep custom attributes and weak references
    # working (the dict is only created if used).
    __slots__ = (
        "__dict__",
        "__weakref__",
        "_dirty",
        "_frames",
        "_is_padded",
        "_ordered",
        "_output",
        "_pad",
        "_pending",
    )

    def __init__(
        self, frames: Frames | None = None, pad: SupportsInt | None = 1
    ) -> None:
        """Initialise the instance."""
        super().__init__()

        # Sorted, unique frames, plus frames added since the last _sync()
        # (unsorted, possibly duplicated or already present).
        self._frames: FrameStore = array.array("q")
        self._pending: FrameStore = array.array("q")
        # Whether _pending is strictly increasing.
        self._ordered = True
        self._dirty = True
        self._is_padded = False
        self._output = ""
        # 0 means "not set yet": a frame sequence string sets it from its
        # first frame.
        self._pad = 0

        if isinstance(frames, str):
            if not self.is_frame_sequence(frames):
                raise ValueError(
                    f"Invalid iterable specified ({type(frames)}, {frames!r})"
                )
            self._add_frame_sequence(frames)
            return

        if isinstance(frames, (FrameChunk, FrameSequence)):
            pad = frames.pad
        elif frames is None:
            frames = []
        elif not _is_iterable(frames):
            frames = [frames]

        self.pad = pad
        self._add_from_iterable(frames)  # type: ignore[arg-type]

    def __setstate__(self, state: Any) -> None:
        """Unpickle, including pickles made by seqparse 1.0.x."""
        if isinstance(state, tuple):
            seqparse.restore_slots(self, state)
        else:
            self._set_legacy_state(state)

    def _set_legacy_state(self, state: dict[str, Any]) -> None:
        """Restore the plain-dict state that seqparse 1.0.x pickled."""
        self._frames = _compact(sorted(state["_data"]))
        self._pending = array.array("q")
        self._ordered = True
        self._dirty = True
        self._is_padded = False
        self._output = ""
        self.pad = state["_attrs"]["pad"]

    def __contains__(self, item: object) -> bool:
        """Defining containment logic (per standard set)."""
        number = _contained_frame(item)
        if number is None or not self._has(number):
            return False
        if isinstance(item, str):
            return _is_correctly_padded(item, self._pad)
        return True

    def __iter__(self) -> Iterator[str]:
        """Defining item iteration logic (per standard set)."""
        if self._dirty:
            self.calculate()

        spec = f"0{self._pad}d"
        # Iterate a copy, so changing the sequence mid-loop is safe.
        for frame in self._frames[:]:
            yield format(frame, spec)

    def __len__(self) -> int:
        """Defining item length logic (per standard set)."""
        self._sync()
        return len(self._frames)

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return (
            f"{type(self).__name__}(pad={self._pad:d}, "
            f"frames=set({self._sorted_frames()!r}))"
        )

    def __reversed__(self) -> Iterator[str]:
        """Allow reversed iteration via reversed()."""
        return reversed(list(self))

    def __str__(self) -> str:
        """String reprentation of the frame sequence."""
        self.calculate()
        return self._output

    @property
    def is_dirty(self) -> bool:
        """bool: Whether output needs to be recalculated after an update."""
        return self._dirty

    @property
    def is_padded(self) -> bool:
        """bool: Whether the FrameSequence contains any zero-padded frames."""
        self.calculate()
        return self._is_padded

    @property
    def pad(self) -> int:
        """
        int: Zero-padding for the frames contained by the object.

        Minimum acceptable value for pad is 1.
        """
        return self._pad

    @pad.setter
    def pad(self, val: SupportsInt | None) -> None:
        self._pad = max(1, int(val or 1))
        self._dirty = True  # the output's padding changes

    def add(self, value: Frames) -> None:
        """Defining value addition logic (per standard set)."""
        if type(value) is int:
            self._push(value)

        elif isinstance(value, str):
            # isdecimal() accepts exactly the digits the frame regex's \d
            # does, so a single frame skips the regex entirely.
            if value.isdecimal():
                self._check_pad(value, strict=False)
                self._push(int(value))
            elif self.is_frame_sequence(value):
                self._add_frame_sequence(value)
                return
            else:
                raise ValueError(f"Invalid value specified ({value!r})")

        elif isinstance(value, (FrameChunk, FrameSequence)):
            if value.pad != self._pad:
                raise SeqparsePadError(
                    f"Specified value ({value!r}) is incorrectly padded "
                    f"({value.pad:d} != {self._pad:d})"
                )
            # Same pad, so every frame is valid: add the integers directly.
            # (FileSequence iterates file names, so it keeps the slow path.)
            if type(value) is FrameChunk:
                self._extend(
                    range(value.first, value.last + 1, value.step), True
                )
            elif type(value) is FrameSequence:
                value._sync()
                self._extend(value._frames, True)
            else:
                self._add_from_iterable(value)

        elif _is_iterable(value):
            self._add_from_iterable(value)  # type: ignore[arg-type]

        else:
            self._push(_frame_number(value))

        self._dirty = True

    def discard(self, value: SupportsInt | str) -> None:
        """Defining item discard logic (per standard set)."""
        if isinstance(value, str):
            self._check_pad(value, strict=False)
            number: int | None = int(value)
        else:
            number = _exact_frame(value)
        self._dirty = True
        if number is None:
            return  # not a frame number (eg 1.5), so not in the sequence

        self._sync()
        frames = self._frames
        idx = bisect.bisect_left(frames, number)
        if idx < len(frames) and frames[idx] == number:
            del frames[idx]

    def update(self, value: Iterable[Any]) -> None:
        """Defining value update logic (per standard set)."""
        for item in value:
            self.add(item)

    def calculate(self, force: bool = False) -> None:
        """
        Calculate the output file sequence.

        Output string file sequence will always be recalculated if the instance
        has been marked as "dirty" when its contents have been modified by an
        external process.

        Args:
            force (bool, optional): Whether to force recalculation.

        Returns:
            None
        """
        if not (self._dirty or force):
            return

        self._sync()
        self._is_padded = False
        self._output = ""
        frames = self._frames
        num_frames = len(frames)
        if not num_frames:
            return

        spec = f"0{self._pad}d"
        parts: list[str] = []

        def emit(first: int, last: int, length: int, step: int) -> None:
            """Render the run frames[first..last] (indices)."""
            low, high = format(frames[first], spec), format(frames[last], spec)
            if length == 1:
                parts.append(low)
            elif length == 2:  # noqa: PLR2004 - a pair is written "a,b"
                parts.append(f"{low},{high}")
            elif step > 1:
                parts.append(f"{low}-{high}x{step}")
            else:
                parts.append(f"{low}-{high}")

        # Split the sorted frames into runs with a constant step. A run of
        # exactly two frames followed by a different step gives up its second
        # frame to the next run, so [1, 3, 4, 5] renders as "1,3-5" rather
        # than "1,3,4,5".
        start, step = 0, 0
        for idx, gap in enumerate(
            map(operator.sub, itertools.islice(frames, 1, None), frames)
        ):
            if not step:
                step = gap
            elif gap != step:
                if idx - start == 1:
                    emit(start, start, 1, 1)
                    start, step = idx, gap
                else:
                    emit(start, idx, idx - start + 1, step)
                    start, step = idx + 1, 0
        emit(start, num_frames - 1, num_frames - start, step)

        # This will be used by the parent FileExtension instance during the
        # zero-pad consolidation stage of the output process.
        self._is_padded = frames[0] < 10 ** (self._pad - 1)
        self._output = ",".join(parts)
        self._dirty = False

    def invert(self) -> FrameSequence:
        """
        Calculate frames missing from the sequence.

        Returns:
            FrameSequence containing the missing frames (if any).
        """
        self._sync()
        inverted = FrameSequence(pad=self._pad)
        # Gaps between consecutive sorted frames are already sorted and
        # unique, so they go straight into the store (same kind as ours, so
        # anything that fits ours fits it).
        missing = self._frames[:0]
        for low, high in itertools.pairwise(self._frames):
            if high - low > 1:
                missing.extend(range(low + 1, high))
        inverted._frames = missing
        return inverted

    def _has(self, number: int) -> bool:
        """Whether the frame number is in the sequence."""
        self._sync()
        frames = self._frames
        idx = bisect.bisect_left(frames, number)
        return idx < len(frames) and frames[idx] == number

    def _sorted_frames(self) -> list[int]:
        """The frame numbers, sorted."""
        self._sync()
        return list(self._frames)

    def _push(self, number: int) -> None:
        """Queue one frame number for addition."""
        pending = self._pending
        if pending and number <= pending[-1]:
            self._ordered = False
        try:
            pending.append(number)
        except OverflowError:
            self._pending = pending = list(pending)
            pending.append(number)

    def _extend(self, numbers: Iterable[int], ordered: bool = False) -> None:
        """
        Queue frame numbers for addition.

        Args:
            numbers (iterable of int): Frame numbers to add.
            ordered (bool, optional): Whether numbers is strictly increasing.
        """
        pending = self._pending
        if ordered and pending:
            first = next(iter(numbers), None)
            ordered = first is None or first > pending[-1]
        if not ordered:
            self._ordered = False
        try:
            pending.extend(numbers)
        except OverflowError:
            # Some numbers may already be in: duplicates are harmless.
            self._ordered = False
            self._pending = pending = list(pending)
            pending.extend(numbers)
        self._dirty = True

    def _sync(self) -> None:
        """Merge pending frames into the sorted, unique frame store."""
        pending = self._pending
        if not pending:
            return
        frames = self._frames
        ordered = self._ordered
        self._pending = array.array("q")
        self._ordered = True
        try:
            if ordered and (not frames or frames[-1] < pending[0]):
                frames.extend(pending)
                return
            if len(pending) <= _SMALL_MERGE:
                for number in pending:
                    idx = bisect.bisect_left(frames, number)
                    if idx == len(frames) or frames[idx] != number:
                        frames.insert(idx, number)
                return
        except OverflowError:
            pass  # a frame is too big for the array: rebuild below
        merged = set(frames)
        merged.update(pending)
        self._frames = _compact(sorted(merged))

    def _add_from_iterable(self, iterable: Iterable[Any]) -> None:
        """
        Add items from supplied iterable to the instance.

        Args:
            iterable (many types): Iterable (usually a list-list object) from
                which you'd like to add items to the instance.

        Returns:
            None
        """
        if (
            isinstance(iterable, (FrameChunk, FrameSequence))
            and type(iterable) in (FrameChunk, FrameSequence)
            and iterable.pad == self._pad
        ):
            self.add(iterable)  # integer fast path, no string round trip
            return
        if isinstance(iterable, array.array) and iterable.typecode == "q":
            self._extend(iterable)
            return
        if isinstance(iterable, range):
            self._extend(iterable, iterable.step > 0)
            return
        if isinstance(iterable, (list, tuple, set, frozenset)):
            # array() converts in C and rejects anything that isn't an
            # integer (strings need pad checks; floats, huge ints, ...),
            # which then takes the general path below.
            try:
                numbers = array.array("q", iterable)
            except (TypeError, OverflowError):
                pass
            else:
                # Sorted input (common) skips the merge's temporary set.
                ordered = not isinstance(iterable, (set, frozenset)) and all(
                    map(
                        operator.lt, numbers, itertools.islice(numbers, 1, None)
                    )
                )
                self._extend(numbers, ordered)
                return
        for item in iterable:
            self.add(item)

    def _add_frame_sequence(self, frame_seq: str) -> None:
        """
        Add a string frame sequence to the instance.

        Args:
            frame_seq (str): frame sequence that you'd like to add to the
                instance.

        Returns:
            None
        """
        # Callers have already validated frame_seq against the frame sequence
        # regex, so each chunk is exactly "first[-last[xstep]]".
        self._dirty = True
        pending = self._pending
        ordered = self._ordered
        try:
            for bit in frame_seq.split(","):
                if not bit:
                    continue

                first, _, rest = bit.partition("-")
                last, _, step = rest.partition("x")
                if not self._pad:
                    self.pad = len(first)

                self._check_pad(first)
                if last:
                    self._check_pad(last)

                low = int(first)
                high = int(last) if last else low
                if high < low:
                    raise ValueError(
                        "Last frame is less than first frame: "
                        f"{high:d} < {low:d}"
                    )
                frames = range(low, high + 1, max(1, int(step or 1)))
                if ordered and pending and low <= pending[-1]:
                    ordered = False
                try:
                    pending.extend(frames)
                except OverflowError:
                    ordered = False
                    self._pending = pending = list(pending)
                    pending.extend(frames)
        finally:
            # Frames added before an error stay added (as before).
            self._ordered = ordered

    def _check_pad(self, value: str, strict: bool = True) -> None:
        """
        Raise SeqparsePadError if a string frame is incorrectly padded.

        Args:
            value (str): String frame to validate against the instance's pad.
            strict (bool, optional): Whether to also reject frames without
                leading zeros that are shorter than the pad. Defaults to True.

        Returns:
            None
        """
        if strict:
            valid = _is_correctly_padded(value, self._pad)
        else:
            valid = not value.startswith("0") or len(value) == self._pad
        if not valid:
            raise SeqparsePadError(
                f"Specified value ({value!r}) is incorrectly padded "
                f"({len(value):d} != {self._pad:d})"
            )


###############################################################################
# Class: FileSequence


class FileSequence(FrameSequence):
    """
    Representative for sequences of files.

    You may create a new instance of this class a couple of ways:

    1. Either clone a new instance from an existing one ...

        >>> parent = FileSequence(frames="0001-0003", ext="exr")
        >>> clone = FileSequence(parent)
        >>> clone == parent
        True

    2. ... or create a valid instance by providing a file extension and at
       least one frame (the base name is optional in every sense of the word):

       >>> fseq = FileSequence(frames="0001", ext="exr")
       >>> print(fseq)
       0001.exr

    Args:
        name (str, optional): Base name (including containing directory) for
            the file sequence.
        frames (many types, optional): Initial frame range to store in the
            instance. Acceptable input types include FrameChunk, FrameSequence
            instances, string representation of a frame sequence, list, set, or
            tuple of integer frames.
        ext (str, optional): File extension for the sequence.
        pad (int, optional): Frame padding for the sequence. Defaults to 1.
    """

    __slots__ = (
        "_ctime",
        "_ext",
        "_full",
        "_mtime",
        "_name",
        "_path",
        "_size",
        "_stat",
    )

    # Mutable, and equality depends on mutable state: deliberately
    # unhashable (like set and dict).
    __hash__ = None  # type: ignore[assignment]

    def __init__(
        self,
        name: FileSequence | str | None = None,
        frames: Frames | None = None,
        ext: str | None = None,
        pad: SupportsInt | None = 1,
    ) -> None:
        """Initialise the instance."""
        self._ctime: float | None = None
        self._mtime: float | None = None
        self._size: int | None = None
        self._ext: str | None = None
        self._full = ""
        self._name: str | None = None
        self._path: str | None = None
        self._stat: dict[int, os.stat_result] = {}

        source = None
        if isinstance(name, FileSequence):
            source = name
            name = None
            frames, ext, pad = source._sorted_frames(), source.ext, source.pad
        elif name:
            # Only treat the name as a complete file sequence string when no
            # frames are given and any given extension agrees with it;
            # otherwise base names that happen to look like file sequences
            # (eg "comp.1.final") would be mangled.
            file_seq_bits = None
            if isinstance(name, str) and frames is None:
                file_seq_bits = self.file_seq_match(name)
                if file_seq_bits and ext not in (None, file_seq_bits.ext):
                    file_seq_bits = None
            if file_seq_bits:
                name, frames, ext = file_seq_bits
                pad = None

        super().__init__(frames, pad=pad)

        self.ext = ext
        if source is not None:
            self.path = source.path
            self.name = source.name
            self._stat.update(source.stat())
        else:
            self.name = name

    def _set_legacy_state(self, state: dict[str, Any]) -> None:
        """Restore the plain-dict state that seqparse 1.0.x pickled."""
        super()._set_legacy_state(state)
        info = state["_info"]
        self._ext, self._full = info["ext"], info["full"]
        self._name, self._path = info["name"], info["path"]
        self._stat = state["_stat"]
        self._ctime = self._mtime = self._size = None

    def __contains__(self, item: object) -> bool:
        """Defining containment logic (per standard set)."""
        if str(item).isdigit():
            return super().__contains__(item)
        if not isinstance(item, str):
            return item in set(self)
        number = self._frame_of_name(item)
        return number is not None and self._has(number)

    def _frame_of_name(self, item: str) -> int | None:
        """
        The frame number of a file name that is shaped like our files.

        A name is shaped like ours when it is prefix + padded frame + suffix;
        check that directly instead of building every file name. Whether the
        frame is actually in the sequence is up to the caller.
        """
        if os.altsep:  # Windows: either separator names the same file
            item = item.replace(os.altsep, os.sep)
        prefix, suffix = self._name_affixes()
        if len(item) <= len(prefix) + len(suffix):
            return None
        if not (item.startswith(prefix) and item.endswith(suffix)):
            return None
        frame = item[len(prefix) : len(item) - len(suffix)]
        digits = frame.removeprefix("-")  # negative frames render as "-005"
        if not (digits.isascii() and digits.isdigit()):
            return None
        number = int(frame)
        return number if frame == f"{number:0{self._pad}d}" else None

    def __eq__(self, other: object) -> bool:
        """Define equality between instances."""
        if type(other) is type(self):
            return super().__eq__(other)
        return False

    def __iter__(self) -> Iterator[str]:
        """Defining item iteration logic (per standard set)."""
        prefix, suffix = self._name_affixes()
        for frame in super().__iter__():
            yield f"{prefix}{frame}{suffix}"

    def __repr__(self) -> str:  # pragma: no cover
        """Pretty representation of the instance."""
        return (
            f"{type(self).__name__}(full_name={self._full!r}, "
            f"ext={self._ext!r}, pad={self._pad}, "
            f"frames=set({self._sorted_frames()!r}))"
        )

    def __str__(self) -> str:
        """String reprentation of the frame sequence."""
        frames = super().__str__()
        return self._get_sequence_output(frames)

    @property
    def ctime(self) -> float | None:
        """
        int: Most recent inode or file change time for a file in the sequence.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._ctime

    @property
    def ext(self) -> str | None:
        """str: File extension for the sequence."""
        return self._ext

    @ext.setter
    def ext(self, val: object) -> None:
        self._ext = str(val) if val else None

    @property
    def frames(self) -> Iterator[str]:
        """iterator(str): the file sequence's padded frames."""
        yield from super().__iter__()

    @property
    def pretty_frames(self) -> str:
        """str: pretty representation of the file sequence's print frames."""
        return super().__str__()

    @property
    def full_name(self) -> str:
        """str: Full name of the sequence, including containing directory."""
        return self._full

    @property
    def mtime(self) -> float | None:
        """
        int: Most recent file modification time for a file in the sequence.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._mtime

    @property
    def name(self) -> str | None:
        """
        str: Base name of the file sequence (no containing directory).

        Note: Setting this property will modify both the `full_path` and `path`
        properties.
        """
        return self._name

    @name.setter
    def name(self, val: object) -> None:
        self._name = None
        text = str(val) if val else ""
        if text:
            # If it's a file path (complete with directory prefix), set the
            # path property as well.
            if os.sep in text or (os.altsep and os.altsep in text):
                path_name, text = os.path.split(os.path.normpath(text))
                self.path = path_name
            self._name = text

        self._full = os.path.join(self._path or "", text)

    @property
    def path(self) -> str | None:
        """
        str: Directory in which the contained files are located.

        Note: Setting the `name` property will reset the contained value.
        """
        return self._path

    @path.setter
    def path(self, val: str | os.PathLike[str] | None) -> None:
        self._path = str(os.path.normpath(val)) if val else None
        self._full = os.path.join(self._path or "", self._name or "")

    @property
    def size(self) -> int | None:
        """
        int: Total size of the file sequence in bytes.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._size

    def discard(self, value: SupportsInt | str) -> None:
        """
        Remove a frame if it is in the sequence (per standard set).

        Args:
            value: A frame number, a frame string, or the file name of one of
                the sequence's files (what iterating gives). The name of a
                file that is not in the sequence is ignored if it is shaped
                like the sequence's files; any other string raises ValueError.
        """
        if isinstance(value, str) and not value.isdigit():
            # Iterating gives file names, so the standard set methods that
            # hand those back (pop, clear, -=, remove) must work with them.
            named = self._frame_of_name(value)
            if named is not None:
                value = named
        super().discard(value)
        number = int(value) if isinstance(value, str) else _exact_frame(value)
        if number is not None and self._stat.pop(number, None) is not None:
            self._dirty = True  # the cached aggregates covered this stat

    def update(self, iterable: Iterable[Any]) -> None:
        """Defining item update logic (per standard set)."""
        if isinstance(iterable, FileSequence):
            for attr in ("ext", "full_name"):
                iterable_value = getattr(iterable, attr)
                self_value = getattr(self, attr)
                if iterable_value != self_value:
                    raise ValueError(
                        "Attribute mismatch on supplied FileSequence "
                        f"instance ({attr}): self:{self_value!r} != "
                        f"iterable:{iterable_value!r}"
                    )

            self._stat.update(iterable.stat())
            self._dirty = True  # the cached aggregates predate these stats
            # Frames are valid for this pad unless they carry leading zeros
            # of a different width; then take the slow path (which raises).
            iterable._sync()
            other = iterable._frames
            if other and (
                iterable.pad == self._pad
                or other[0] >= 10 ** (iterable.pad - 1)
            ):
                self._extend(other, True)
                return
            iterable = iterable.frames

        for item in iterable:
            self.add(item)

    def cache_stat(
        self, frame: SupportsInt | str, input_stat: seqparse.StatLike
    ) -> os.stat_result:
        """
        Cache file system stat data for the specified frame.

        Input disk stat value will be stored in a new stat_result
        instance.

        Args:
            frame (int): Frame for which you'd like to cache the supplied stat
                data.
            input_stat (stat_result): Value that you'd like to cache.

        Returns:
            stat_result that was successfully cached.
        """
        number = int(frame)
        self._stat[number] = seqparse.get_stat_result(input_stat)
        self._dirty = True  # size/mtime/ctime aggregate the cached stats
        return self._stat[number]

    def calculate(self, force: bool = False) -> None:
        """
        Calculate the output file sequence.

        Output string file sequence will always be recalculated if the instance
        has been marked as "dirty" when its contents have been modified by an
        external process.

        Args:
            force (bool, optional): Whether to force recalculation.

        Returns:
            None
        """
        if not (self._dirty or force):
            return

        super().calculate(force=force)

        # Cache disk stats for easy/quick access via property ...
        self._aggregate_stats()

    def invert(self) -> FileSequence:
        """
        Calculate file names missing from the sequence.

        Returns:
            FileSequence containing the missing files (if any).
        """
        frames = super().invert()
        inverted = FileSequence(frames=frames, ext=self._ext, pad=frames.pad)
        inverted.path = self._path
        inverted.name = self._name
        return inverted

    def empty_files(self) -> FileSequence:
        """
        Find the zero-byte files in the sequence.

        Only frames whose disk stats are already cached (see `stat`) can be
        found, so scan with disk stats enabled first; a frame without cached
        stats is never reported.

        Returns:
            FileSequence containing the empty files (if any), with their
            cached stats.
        """
        empty = [
            number
            for number, info in self._stat.items()
            if info.st_size == 0 and self._has(number)
        ]
        found = FileSequence(frames=empty, ext=self._ext, pad=self.pad)
        found.path = self._path
        found.name = self._name
        for number in empty:
            found.cache_stat(number, self._stat[number])
        return found

    @overload
    def stat(self) -> dict[int, os.stat_result]: ...
    @overload
    def stat(
        self, frame: SupportsInt | str, force: bool = ..., lazy: bool = ...
    ) -> os.stat_result | None: ...
    @overload
    def stat(
        self,
        frame: SupportsInt | str | None = ...,
        force: bool = ...,
        lazy: bool = ...,
    ) -> dict[int, os.stat_result] | os.stat_result | None: ...
    def stat(
        self,
        frame: SupportsInt | str | None = None,
        force: bool = False,
        lazy: bool = False,
    ) -> dict[int, os.stat_result] | os.stat_result | None:
        """
        Individual frame file system status.

        Args:
            frame (int, optional): Frame for which you'd like to return the
                disk stats.
            force (bool, optional): Whether to force disk stat query,
                regardless of caching status.
            lazy (bool, optional): Whether to query disk stats should no cached
                value exist.

        Returns:
            None if a frame has been specified but disk stats have not been
            cached.
            stat_result if a frame has been specified and disk stats have
            been previously cached.
            dict of disk stats, indexed by int frame if no frame has been
            specified.
        """
        if frame is None:
            if force or lazy:
                raise ValueError(
                    "Must specify frame when querying for file disk stats."
                )
            return self._stat

        number = int(frame)
        if force or (lazy and self._stat.get(number) is None):
            file_name = self._get_sequence_output(number)
            self.cache_stat(number, os.stat(file_name))

        return self._stat.get(number, None)

    def _aggregate_stats(self) -> None:
        """
        Aggregate stats for a variety of file sequence properties.

        This method clears all cached aggregate values before recalculating
        new values.

        Returns:
            None
        """
        self._ctime = self._mtime = self._size = None

        stats = self._stat
        if not stats:
            return

        ctime: float = 0
        mtime: float = 0
        size = 0
        self._sync()
        for frame in self._frames:
            stat = stats.get(frame)
            if stat is None:
                continue
            ctime = max(ctime, stat.st_ctime)
            mtime = max(mtime, stat.st_mtime)
            size += stat.st_size

        self._ctime, self._mtime, self._size = ctime, mtime, size

    def _name_affixes(self) -> tuple[str, str]:
        """
        Calculate the text surrounding the frame in this sequence's names.

        Returns:
            tuple of (prefix, suffix) such that prefix + padded frame + suffix
            is a member file name (matches _get_sequence_output for digits).
        """
        name = f"{self._name}." if self._name else ""
        return os.path.join(self._path or "", name), f".{self._ext}"

    def _get_sequence_output(self, frames: str | int | None) -> str:
        """
        Calculate a valid file sequence string from the given iterator.

        Args:
            frames (str): String representation of a frame sequence.

        Returns:
            str representation of a file sequence.
        """
        if frames is None or frames == "":
            return ""

        if str(frames).isdigit():
            frames = f"{int(frames):0{self._pad}d}"
        elif not self._ext:
            raise ValueError("File sequence extension has not been defined.")

        if self._name:
            file_name = f"{self._name}.{frames}.{self._ext}"
        else:
            file_name = f"{frames}.{self._ext}"
        return os.path.join(self._path or "", file_name)
