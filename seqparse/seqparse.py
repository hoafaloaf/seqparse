"""The main engine for the seqparse module."""

# Standard Libraries
import os
from collections import defaultdict

# Third Party Libraries
import scandir

from .containers import FileSequenceContainer, SingletonContainer
from .regex import SeqparseRegexMixin
from .sequences import FrameChunk

__all__ = ("Seqparse", )

###############################################################################
# Class: Seqparse


class Seqparse(SeqparseRegexMixin):
    """Storage and parsing engine for file sequences."""

    def __init__(self):
        """Initialise the instance."""
        super(Seqparse, self).__init__()

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
        file_seq_bits = self.file_seq_match(str(file_name))

        if file_seq_bits:
            base_name, frames, file_ext = file_seq_bits
            dir_name, base_name = os.path.split(base_name)

            loc = self.locations[dir_name]
            sequence = loc["seqs"][base_name]

            # Set the name and path properties at initialization.
            if not sequence:
                sequence.name = base_name
                sequence.path = dir_name

            # We'll assume that a frame sequence is properly formed -- and use
            # the length of the first frame as the padding. The FrameSequence
            # to which we're adding the frames will do the actual validation.
            for chunk in frames.split(","):
                bits = self.bits_match(chunk, as_dict=True)
                pad = len(bits["first"])
                break

            ext = sequence[file_ext]
            ext[pad].add(frames)

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

    def output(self, missing=False, seqs_only=False):
        """Yield a list of contained singletons and file sequences."""
        for root_dir in sorted(self.locations):
            data = self.locations[root_dir]
            for container in sorted(data["seqs"].values()):
                for file_seq in container.output():
                    if missing:
                        yield file_seq.invert()
                    else:
                        yield file_seq

            if seqs_only:
                continue

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

    def _get_data(self, typ):
        """Return dictionary of the specified data type from the instance."""
        output = dict()
        for loc, data in self.locations.iteritems():
            if data[typ]:
                output[loc] = data[typ]

        return output

    def validate_frame_sequence(self, frame_seq):
        """Whether the supplied frame (not file) sequence is valid."""
        if self.is_frame_sequence(frame_seq):
            bits = list()
            for bit in frame_seq.split(","):
                if not bit:
                    continue

                first, last, step = self.bits_match(bit)

                try:
                    chunk = FrameChunk(first, last, step, len(first))
                except ValueError:
                    return None

                bits.append(str(chunk))

            # Looks good!
            return ",".join(bits)

        return None
