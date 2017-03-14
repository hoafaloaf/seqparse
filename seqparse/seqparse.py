"""The main engine for the seqparse module."""

# Standard Libraries
import os
import re
from collections import defaultdict

# Third Party Libraries
import scandir

from .classes import FileSequence, FrameChunk, Singletons

__all__ = ("Seqparse", )

# TODO: Add support for ...
# 1. Negative increments
# 2. Negative frame numbers

###############################################################################
# Class: Seqparse


class Seqparse(object):
    """Storage and parsing engine for file sequences."""

    BITS_EXPR = re.compile(
        r"(?P<first>\d+)(?:-(?P<last>\d+)(?:x(?P<incr>\d+)?)?)?$")
    FILE_EXPR = re.compile(r"(?P<base>.*)\.(?P<frame>\d+)\.(?P<ext>[^\.]+)$")
    SEQ_EXPR = re.compile(
        r",*(\d+(?:-\d+(?:x\d+)?)?(?:,+\d+(?:-\d+(?:x\d+)?)?)*),*$")

    def __init__(self):
        """Initialise the instance."""
        self._locs = defaultdict(
            lambda: dict(seqs=defaultdict(FileSequence), files=Singletons()))

    @property
    def locations(self):
        """A dictionary of tracked singletons and file sequences."""
        return self._locs

    @property
    def sequences(self):
        """A dictionary of tracked file sequences."""
        return self._get_data("seqs")

    @property
    def singletons(self):
        """A dictionary of tracked singleton files."""
        return self._get_data("files")

    def add_file(self, file_name):
        """Add a file to the parser instance."""
        smatch = self.FILE_EXPR.match(str(file_name))

        if smatch:
            base_name, frame, file_ext = smatch.groups()
            dir_name, base_name = os.path.split(base_name)

            loc = self.locations[dir_name]
            sequence = loc["seqs"][base_name]

            # Set the name and path properties at initialization.
            if not sequence:
                sequence.name = base_name
                sequence.path = dir_name

            ext = sequence[file_ext]
            pad = len(frame)
            ext[pad].add(frame)

        else:
            dir_name, base_name = os.path.split(file_name)
            loc = self.locations[dir_name]

            singletons = loc["files"]

            # Set the path properties at initialization.
            if not singletons:
                singletons.path = dir_name

            singletons.add(base_name)

    def add_from_scan(self, root, file_names):
        """Shortcut for adding file sequences from os/scandir.walk."""
        root = str(root)

        for file_name in file_names:
            self.add_file(os.path.join(root, file_name))

    # TODO: Implement tree option.
    # def output(self, tree=False):
    def output(self):
        """Yield a list of contained file sequences and singletons."""
        for data in sorted(self.locations.values()):
            for file_seq in sorted(data["seqs"].values()):
                for seq_name in file_seq.output():
                    yield seq_name

            for file_name in sorted(data["files"].output()):
                yield file_name

    def scan_path(self, search_path, level=0):
        """Scan supplied path, add all discovered files to the instance."""
        search_path = search_path.rstrip(os.path.sep)
        search_seps = search_path.count(os.path.sep)

        for root, dir_names, file_names in scandir.walk(search_path):
            # Cheap and easy way to limit our search depth: count path
            # separators!
            cur_level = root.count(os.path.sep) - search_seps
            if level > 0 and cur_level >= level:
                continue
            self.add_from_scan(root, file_names)

    def _get_data(self, typ):
        """Return dictionary of the specified data type from the instance."""
        output = dict()
        for loc, data in self.locations.iteritems():
            if data[typ]:
                output[loc] = data[typ]

        return output

    @classmethod
    def validate_frame_sequence(cls, frame_seq):
        """Whether the supplied frame (not file) sequence is valid."""
        if cls.SEQ_EXPR.match(frame_seq):
            bits = list()
            for bit in frame_seq.split(","):
                if not bit:
                    continue

                first, last, step = cls.BITS_EXPR.match(bit).groups()

                try:
                    chunk = FrameChunk(first, last, step, len(first))
                except ValueError:
                    return None

                bits.append(str(chunk))

            # Looks good!
            return ",".join(bits)

        return None
