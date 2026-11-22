"""Container for all regular expressions used by the seqparse module."""

from __future__ import annotations

import re
from typing import ClassVar, Literal, NamedTuple, overload

__all__ = (
    "BITS_EXPR",
    "FILE_NAME_EXPR",
    "FILE_SEQ_EXPR",
    "FRAME_EXPR",
    "SeqparseRegexMixin",
)

# BITS_EXPR is used to split a frame "chunk" into three sections: first
# (frame), last (frame). and step.
BITS_EXPR = r"(?P<first>\d+)(?:-(?P<last>\d+)(?:x(?P<step>\d+)?)?)?$"

# FILE_NAME_EXPR is used to split a file name into three sections: base (name),
# frame (chunk), and file ext(ension).
FILE_NAME_EXPR = r"(?:^(?P<name>.+)\.|^)(?P<frame>\d+)\.(?P<ext>[^\.]+)$"

# FRAME_EXPR is used to validate a "legal" sequence of frames.
FRAME_EXPR = r"(?:\d+(?:-\d+(?:x\d+)?)?(?:,+\d+(?:-\d+(?:x\d+)?)?)*)"

# FILE_SEQ_EXPR is used to validate and split a "legal" sequence of files into
# three sections: base (name), frame (sequence), and file ext(ension).
FILE_SEQ_EXPR = (
    rf"(?:^(?P<name>.+)\.|^)(?P<frames>{FRAME_EXPR})\.(?P<ext>[^\.]+)$"
)

# The same grammar with possessive quantifiers, for matching: it never needs
# to backtrack (digits are always followed by "-", "x", "," or what follows
# the frames), and without them the regex engine keeps a backtracking state
# per chunk (~23 MB for a 50k-chunk sequence).
_FRAME_POSSESSIVE = (
    r"\d++(?:-\d++(?:x\d++)?+)?+(?:,++\d++(?:-\d++(?:x\d++)?+)?+)*+"
)

GroupDict = dict[str, str | None]


class ChunkBits(NamedTuple):
    """The parts of a frame chunk: "first[-last[xstep]]"."""

    first: str
    last: str | None
    step: str | None


class FileNameBits(NamedTuple):
    """The parts of a single-frame file name: "[name.]frame.ext"."""

    name: str | None
    frame: str
    ext: str


class SequenceBits(NamedTuple):
    """The parts of a file sequence string: "[name.]frames.ext"."""

    name: str | None
    frames: str
    ext: str


###############################################################################
# Class: SeqparseRegexMixin
class SeqparseRegexMixin:
    """Base for classes that need to perform regular expression matches."""

    __slots__ = ()

    _bits_expr: ClassVar[re.Pattern[str]] = re.compile(BITS_EXPR)
    _file_expr: ClassVar[re.Pattern[str]] = re.compile(FILE_NAME_EXPR)
    _frame_expr: ClassVar[re.Pattern[str]] = re.compile(
        rf",*+{_FRAME_POSSESSIVE},*+$"
    )
    _fseq_expr: ClassVar[re.Pattern[str]] = re.compile(
        FILE_SEQ_EXPR.replace(FRAME_EXPR, _FRAME_POSSESSIVE)
    )

    @overload
    def bits_match(
        self, val: str, as_dict: Literal[False] = False
    ) -> ChunkBits | None: ...
    @overload
    def bits_match(
        self, val: str, as_dict: Literal[True]
    ) -> GroupDict | None: ...
    def bits_match(
        self, val: str, as_dict: bool = False
    ) -> ChunkBits | GroupDict | None:
        """
        Calculate first, last, step for valid string frame chunks.

        Args:
            val (str): Input chunk of a frame range.
            as_dict (bool, optional): Whether to output return values as a
                dict of regex groups. Defaults to False.

        Returns:
            None if input is an invalid chunk,
            tuple consisting of (first frame, last frame, frame step) with
            as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        bmatch = self._bits_expr.match(val)
        if not bmatch:
            return None
        groups = bmatch.groupdict()
        return groups if as_dict else ChunkBits(**groups)

    @overload
    def file_name_match(
        self, val: str, as_dict: Literal[False] = False
    ) -> FileNameBits | None: ...
    @overload
    def file_name_match(
        self, val: str, as_dict: Literal[True]
    ) -> GroupDict | None: ...
    def file_name_match(
        self, val: str, as_dict: bool = False
    ) -> FileNameBits | GroupDict | None:
        """
        Calculate base name, frame, extension for valid string file name.

        Args:
            val (str): Input file name.
            as_dict (bool, optional): Whether to output return values as a
                dict of regex groups. Defaults to False.

        Returns:
            None if input is an invalid sequence file name,
            tuple consisting of (base name, frame, extension) with
            as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        fmatch = self._file_expr.match(val)
        if not fmatch:
            return None
        groups = fmatch.groupdict()
        return groups if as_dict else FileNameBits(**groups)

    @overload
    def file_seq_match(
        self, val: str, as_dict: Literal[False] = False
    ) -> SequenceBits | None: ...
    @overload
    def file_seq_match(
        self, val: str, as_dict: Literal[True]
    ) -> GroupDict | None: ...
    def file_seq_match(
        self, val: str, as_dict: bool = False
    ) -> SequenceBits | GroupDict | None:
        """
        Calculate base name, sequence, extension for valid file sequence.

        Args:
            val (str): Input file sequence.
            as_dict (bool, optional): Whether to output return values as a
                dict of regex groups. Defaults to False.

        Returns:
            None if input is an invalid sequence file sequence,
            tuple consisting of (base name, frame sequence, extension) with
            as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        fmatch = self._fseq_expr.match(val)
        if not fmatch:
            return None
        groups = fmatch.groupdict()
        return groups if as_dict else SequenceBits(**groups)

    def is_frame_sequence(self, val: str) -> bool:
        """
        Whether a string frame sequence is valid.

        Args:
            val (str): Input frame sequence.

        Returns:
            True if frame sequence is valid, False if it is not.
        """
        return bool(self._frame_expr.match(val))
