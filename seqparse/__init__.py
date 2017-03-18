"""Seqparse: A nifty way to list your file sequences."""

from .seqparse import Seqparse
from .sequences import FrameChunk, FrameSequence

__all__ = ("get_parser", "get_sequence", "invert", "validate_frame_sequence")

###############################################################################
# EXPORTED METHODS


def get_parser():
    """Return a new Seqparse instance."""
    return Seqparse()


def get_sequence(frames, pad=1):
    """Return a new FrameSequence instance."""
    return FrameSequence(frames, pad=pad)


def invert(iterable):
    """Return an iterator representing a sequence's missing frames or files."""
    if not isinstance(iterable, (FrameChunk, FrameSequence)):
        raise TypeError(
            "Only able to invert FrameChunk and FrameSequence instances.")

    return iterable.invert()


def validate_frame_sequence(frame_seq):
    """Whether the supplied frame (not file) sequence is valid."""
    return Seqparse.validate_frame_sequence(frame_seq)
