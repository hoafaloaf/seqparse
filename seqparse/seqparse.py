"""The main engine for the seqparse module."""

# Standard Libraries
import os
import re
from collections import defaultdict

# Third Party Libraries
import scandir

from .containers import FileSequenceContainer, SingletonContainer
from .regex import BITS_EXPR, FILE_NAME_EXPR, FRAME_EXPR, FRAME_SEQ_EXPR
from .sequences import FrameChunk

__all__ = ("Seqparse", )

###############################################################################
# Class: Seqparse


class Seqparse(object):
    """Storage and parsing engine for file sequences."""

    _bits_expr = re.compile(BITS_EXPR)
    _file_expr = re.compile(FILE_NAME_EXPR)
    _frame_expr = re.compile(r",*%s,*$" % FRAME_EXPR)
    _fseq_expr = re.compile(FRAME_SEQ_EXPR)

    def __init__(self):
        """Initialise the instance."""
        self._locs = defaultdict(
            lambda: dict(
                seqs=defaultdict(FileSequenceContainer),
                files=SingletonContainer()))

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
        fmatch = self._fseq_expr.match(str(file_name))
        smatch = self._file_expr.match(str(file_name))

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

        elif fmatch:
            for file_name in self._iterate_over_sequence(*fmatch.groups()):
                self.add_file(file_name)

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

    def output(self):
        """Yield a list of contained singletons and file sequences."""
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
            if level > 0 and cur_level + 1 == level:
                del dir_names[:]
            self.add_from_scan(root, file_names)

    def _iterate_over_sequence(self, base_name, frame_seq, ext):
        """Iterate with given base name, frame sequence, and file extension."""
        for bit in frame_seq.split(","):
            if not bit:
                continue

            first, last, step = self._bits_expr.match(bit).groups()
            for frame in FrameChunk(first, last, step, len(first)):
                yield ".".join((base_name, frame, ext))

            continue

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
        if cls._frame_expr.match(frame_seq):
            bits = list()
            for bit in frame_seq.split(","):
                if not bit:
                    continue

                first, last, step = cls._bits_expr.match(bit).groups()

                try:
                    chunk = FrameChunk(first, last, step, len(first))
                except ValueError:
                    return None

                bits.append(str(chunk))

            # Looks good!
            return ",".join(bits)

        return None
