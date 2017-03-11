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

    FILE_EXPR = re.compile(r"(?P<base>.*)\.(?P<frame>\d+)\.(?P<ext>[^\.]+)")
    SEQ_EXPR = re.compile(
        r"(\d+(?:-\d+(?:x\d+)?)?(?:,\d+(?:-\d+(?:x\d+)?)?)*)")

    def __init__(self):
        """Initialise the instance."""
        self._locs = defaultdict(
            lambda: dict(seqs=defaultdict(FileSequence), files=set()))

    @property
    def locations(self):
        """A dictionary of tracked singletons and file sequences."""
        return self._locs

    @property
    def sequences(self):
        """A dictionary of tracked file sequences."""
        seqs = dict()
        for loc, data in self.locations.iteritems():
            if data["seqs"]:
                seqs[loc] = data["seqs"]

        return seqs

    @property
    def singletons(self):
        """A dictionary of tracked singleton files."""
        file_names = dict()
        for loc, data in self.locations.iteritems():
            if data["files"]:
                file_names[loc] = data["files"]

        return file_names

    def add_file(self, file_name):
        """Add a file to the parser instance."""
        smatch = self.FILE_EXPR.match(str(file_name))

        if smatch:
            base_name, frame, file_ext = smatch.groups()
            dir_name, base_name = os.path.split(base_name)

            loc = self.locations[dir_name]
            seq = loc["seqs"][base_name]
            seq.name = base_name

            ext = seq[file_ext]
            pad = len(frame)
            ext[pad].add(frame)

        else:
            dir_name, base_name = os.path.split(file_name)
            loc = self.locations[dir_name]
            loc["files"].add(base_name)

    def add_from_walk(self, root, file_names):
        """Shortcut for adding file sequences from os/scandir.walk."""
        root = str(root)

        for file_name in file_names:
            self.add_file(os.path.join(root, file_name))

    # TODO: Implement tree option.
    # def output(self, tree=False):
    def output(self):
        """Yield a list of contained file sequences and singletons."""
        for loc, data in sorted(self.locations.items()):
            for file_seq in sorted(data["seqs"].values()):
                for seq_name in file_seq.output():
                    yield os.path.join(loc, seq_name)

            for file_name in sorted(data["files"]):
                yield os.path.join(loc, file_name)

    def scan_path(self, search_path):
        """Scan supplied path, add all discovered files to the instance."""
        for root, dir_names, file_names in scandir.walk(search_path):
            self.add_from_walk(root, file_names)

    @classmethod
    def validate_frame_sequence(cls, frame_seq):
        """Whether the supplied frame (not file) sequence is valid."""
        if cls.SEQ_EXPR.match(frame_seq):
            return True
        return False
