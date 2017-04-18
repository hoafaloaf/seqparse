"""
seqparse: A nifty way to list your file sequences.

The seqparse module may be used to ...

    * Scan specified paths for file sequences and "singletons,"
    * Construct frame and file sequence from supplied values, and
    * Query disk for overall footprint of tracked files.

The module also comes supplied with a simple command-line tool named "seqls."

Frame sequences are broken down into comma-separated chunks of the format

    (first frame)-(last frame)x(step)

where the following rules apply:

    * Frame numbers can be zero-padded,
    * Frame step (increment) is always a positive integer,
    * The number of digits in a frame may exceed the padding of a sequence, eg
      "001,010,100,1000",
    * Frame chunks with a specified step will *always* consist of three or more
      frames.

Examples of proper frame sequences:

    * Non-padded sequence, frames == (1, 3, 5, 7): 1-7x2
    * Four-padded sequence, frames == (1, 3, 5, 7): 0001-0007x2
    * Three-padded sequence, frames == (11, 13): 011,013
    * Two-padded sequence (1, 3, 5, 7, 11, 13, 102): 01-07x2,11,13,102
"""

# Standard Libraries
import os

__all__ = ("get_parser", "get_sequence", "get_version", "invert",
           "validate_frame_sequence")

###############################################################################
# METADATA

__version__ = "0.7.0"

__title__ = "seqparse"
__description__ = "A nifty way to parse your file sequences."
__uri__ = "http://github.com/hoafaloaf/seqparse"

__author__ = "Geoff Harvey"
__email__ = "hoafaloaf@gmail.com"

__license__ = "MIT"
__copyright__ = "Copyright (c) 2017 {0}".format(__author__)

###############################################################################
# EXPORTED METHODS


def get_parser():
    """
    Create a new Seqparse instance.

    Returns:
        Valid Seqparse instance.

    Examples:
        >>> from seqparse import get_parser
        >>> get_parser()
        Seqparse(sequences=0, singletons=0)
    """
    from .seqparse import Seqparse
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

    Examples:
        >>> from seqparse import get_sequence
        >>> get_sequence(range(5))
        FrameSequence(pad=1, frames=set([0, 1, 2, 3, 4]))
        >>> get_sequence([1, 2, 3])
        FrameSequence(pad=1, frames=set([1, 2, 3]))
        >>> get_sequence("0001-0005x2")
        FrameSequence(pad=4, frames=set([1, 3, 5]))
    """
    from .sequences import FrameSequence
    return FrameSequence(frames, pad=pad)


def get_stat_result(input_stat):
    """
    Wrapper for os-specific stat_result instance.

    Args:
        input_stat (stat_result or stat_result): instance you'd like to clone.

    Returns:
        nt.stat_result or posix.stat_result, dependent on system platform.
    """
    if os.name == "posix":
        from posix import stat_result  # pylint: disable=E0401
    else:  # pragma: no cover
        from nt import stat_result  # pylint: disable=E0401

    return stat_result(input_stat)


def get_version(pretty=False):
    """
    Report which version of seqparse you're using.

    Args:
        pretty (bool) Whether you'd like the super purty, long form version.

    Returns:
        str seqparse version.
    """
    if pretty:
        return "seqls (seqparse-v{})".format(__version__)
    return __version__


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

    Examples:
        >>> from seqparse import get_sequence, invert
        >>> seq = get_sequence("0001-0005x2")
        >>> print repr(seq), str(seq)
        FrameSequence(pad=4, frames=set([1, 3, 5])) 0001-0005x2
        >>> inverted = invert(seq)
        >>> print repr(inverted), str(inverted)
        FrameSequence(pad=4, frames=set([2, 4])) 0002,0004
    """
    from .sequences import FrameChunk, FrameSequence

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

    Examples:
        >>> from seqparse import validate_frame_sequence
        >>> print validate_frame_sequence("0001-0001")
        0001
        >>> print validate_frame_sequence("0001-")
        None
    """
    from .seqparse import Seqparse
    return Seqparse().validate_frame_sequence(frame_seq)
