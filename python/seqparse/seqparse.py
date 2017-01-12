"""The main engine for the seqparse module."""

# Standard Libraries
import re
from collections import defaultdict

from .classes import FileSequence

__all__ = ("Seqparse", )

###############################################################################
# INTERNAL CONSTANTS

SEQ_EXPR = re.compile("^(?P<base>.*)\.(?P<frame>\d+)\.(?P<ext>[^\.]+)$")

###############################################################################
# Class: Seqparse


class Seqparse(object):
    """Storage and parsing engine for file sequences."""

    def __init__(self):
        """Initialise the instance."""
        self._seqs = defaultdict(FileSequence)
        self._singletons = set()

    @property
    def sequences(self):
        """A dictionary of tracked file sequences and singletons."""
        return self._seqs

    def add_from_walk(self, root, file_names):
        """Shortcut for adding file sequences from os/scandir.walk."""
        for file_name in file_names:
            smatch = SEQ_EXPR.match(file_name)
            if smatch:
                base_name, frame, file_ext = smatch.groups()
                seq = self.sequences[base_name]
                ext = seq[file_ext]
                pad = len(frame)

                ext[pad].add(frame)

        print self._seqs['dog']['jpg'][4]
