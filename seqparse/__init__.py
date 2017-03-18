"""Seqparse: A nifty way to list your file sequences."""

from .seqparse import Seqparse
from .classes import FrameChunk

__all__ = ("get_chunk", "get_parser", "validate_frame_sequence")

###############################################################################
# EXPORTED METHODS


def get_chunk(first=None, last=None, step=1, pad=1):
    """Return a new FrameChunk instance."""
    return FrameChunk(first, last=last, step=step, pad=pad)


def get_parser():
    """Return a new Seqparse instance."""
    return Seqparse()


def validate_frame_sequence(frame_seq):
    """Whether the supplied frame (not file) sequence is valid."""
    return Seqparse.validate_frame_sequence(frame_seq)
