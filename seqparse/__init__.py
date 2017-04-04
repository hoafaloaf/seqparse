"""Seqparse: A nifty way to list your file sequences."""

from .seqparse import Seqparse
from .sequences import FrameChunk, FrameSequence

__all__ = ("get_parser", "get_sequence", "invert", "validate_frame_sequence")

###############################################################################
# EXPORTED METHODS


def get_parser():
    """
    Create a new Seqparse instance.

    Returns:
        Valid Seqparse instance.

    >>> from seqparse import get_parser
    >>> get_parser()
    Seqparse(sequences=0, singletons=0)
    """
    return Seqparse()


def get_sequence(frames, pad=1):
    """
    Create a new FrameSequence instance.

    Args:
        frames (str, list, tuple, or set): Either a string representation of a
            valid frame sequence or a list-like iterable of integer frames.
        pad (int, optional): Desired zero-padding for the new FrameSequence
            instance. Defaults to *1*.

    Returns:
        Valid FrameSequence instance.

    >>> from seqparse import get_sequence
    >>> get_sequence(range(5))
    FrameSequence(pad=1, frames=set([0, 1, 2, 3, 4]))
    >>> get_sequence([1, 2, 3])
    FrameSequence(pad=1, frames=set([1, 2, 3]))
    >>> get_sequence("0001-0005x2")
    FrameSequence(pad=4, frames=set([1, 3, 5]))
    """
    return FrameSequence(frames, pad=pad)


def invert(iterable):
    """
    Create an iterator representing a sequence's missing frames or files.

    Args:
        iterable (FrameChunk, FrameSequence, or FileSequence): Iterable that
            you'd like to invert.

    Returns:
        Valid (inverted) FrameSequence from input FrameChunk and FrameSequence
            instances, FileSequence for input FileSequence instances. Note:
            Should the input sequences contain no gaps, will return an empty
            sequence instance.

    >>> from seqparse import get_sequence, invert
    >>> seq = get_sequence("0001-0005x2")
    >>> print repr(seq), str(seq)
    FrameSequence(pad=4, frames=set([1, 3, 5])) 0001-0005x2
    >>> inverted = invert(seq)
    >>> print repr(inverted), str(inverted)
    FrameSequence(pad=4, frames=set([2, 4])) 0002,0004
    """
    if not isinstance(iterable, (FrameChunk, FrameSequence)):
        raise TypeError(
            "Only able to invert FrameChunk and FrameSequence instances.")

    return iterable.invert()


def validate_frame_sequence(frame_seq):
    """
    Whether the supplied string frame (not file) sequence is valid.

    Args:
        frame_seq (str): The frame sequence you'd like to validate.

    Returns:
        None for invalid inputs, corrected/validated str frame sequence for
        valid input (see below for examples).

    >>> from seqparse import validate_frame_sequence
    >>> print validate_frame_sequence("0001-0001")
    0001
    >>> print validate_frame_sequence("0001-")
    None
    """
    return Seqparse().validate_frame_sequence(frame_seq)
