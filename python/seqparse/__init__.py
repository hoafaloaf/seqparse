"""Seqparse: A nifty way to list your file sequences."""

from .seqparse import Seqparse

__all__ = ("get_parser", "validate_frame_sequence")

###############################################################################
# EXPORTED METHODS


def get_parser(*args, **kwargs):
    """Return a new Seqparse instance."""
    return seqparse.Seqparse(*args, **kwargs)


def validate_frame_sequence(frame_seq):
    """Whether the supplied frame (not file) sequence is valid."""
    return seqparse.Seqparse.validate_frame_sequence(frame_seq)
