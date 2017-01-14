"""The main engine for the seqparse module."""

# Standard Libraries
import os
import re
from collections import defaultdict

# Third Party Libraries
import scandir

from .classes import FileSequence

__all__ = ("Seqparse", )

###############################################################################
# Class: Seqparse


class Seqparse(object):
    """Storage and parsing engine for file sequences."""

    FILE_EXPR = re.compile("(?P<base>.*)\.(?P<frame>\d+)\.(?P<ext>[^\.]+)")
    SEQ_EXPR = re.compile("(\d+(?:-\d+(?:x\d+)?)?(?:,\d+(?:-\d+(?:x\d+)?)?)*)")

    def __init__(self):
        """Initialise the instance."""
        self._seqs = defaultdict(FileSequence)
        self._singletons = set()

    @property
    def sequences(self):
        """A dictionary of tracked file sequences."""
        return self._seqs

    @property
    def singletons(self):
        """A set of tracked singleton files."""
        return self._singletons

    def add_file(self, file_name):
        """Add a file to the parser instance."""
        smatch = self.FILE_EXPR.match(str(file_name))

        if smatch:
            base_name, frame, file_ext = smatch.groups()

            seq = self.sequences[base_name]
            seq.name = base_name

            ext = seq[file_ext]
            pad = len(frame)
            ext[pad].add(frame)

        else:
            self._singletons.add(file_name)

    def add_from_walk(self, root, file_names):
        """Shortcut for adding file sequences from os/scandir.walk."""
        root = str(root)

        for file_name in file_names:
            self.add_file(os.path.join(root, file_name))

    def output(self, tree=False):
        """Yield a list of contained file sequences and singletons."""
        for base_name, file_seq in sorted(self.sequences.items()):
            for output in file_seq.output():
                yield output

        for singleton in sorted(self.singletons):
            yield singleton

    def scan_path(self, search_path):
        """Scan supplied path, add all discovered files to the instance."""
        for root, dir_names, file_names in scandir.walk(search_path):
            self.add_from_walk(root, file_names)

    @classmethod
    def validate_frame_sequence(frame_seq):
        """Whether the supplied frame (not file) sequence is valid."""
        if self.SEQ_EXPR.match(frame_seq):
            return True
        return False
