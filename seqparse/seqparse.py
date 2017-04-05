"""The main engine for the seqparse module."""

# Standard Libraries
import os
from collections import defaultdict

from .containers import FileSequenceContainer, SingletonContainer
from .regex import SeqparseRegexMixin
from .sequences import FrameChunk

# Use the built-in version of scandir/walk if possible, otherwise use the
# scandir module version.
try:
    from os import scandir  # pylint: disable=W0611,C0412
except ImportError:
    from scandir import scandir  # pylint: disable=W0611,C0412

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

        self._options = dict(all=False, stat=False)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        num_seqs = len(list(self.output(seqs_only=True)))
        num_files = len(list(self.output())) - num_seqs

        blurb = ("{name}(sequences={seqs}, singletons={files})")
        return blurb.format(
            name=type(self).__name__, files=num_files, seqs=num_seqs)

    @property
    def locations(self):
        """A dictionary of tracked singletons and file sequences."""
        return self._locs

    @property
    def scan_options(self):
        """A dictionary of options used while scanning disk for files."""
        return self._options

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
        entry = None
        if type(file_name).__name__ == "DirEntry":
            entry = file_name
            file_name = file_name.path

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

            # "entry" *should* only ever be defined if it was passed in via the
            # scan_path method.
            if entry and self.scan_options["stat"]:
                ext[pad].cache_stat(
                    int(frames), entry.stat(follow_symlinks=True))

        else:
            dir_name, base_name = os.path.split(file_name)
            loc = self.locations[dir_name]

            singletons = loc["files"]

            # Set the path properties at initialization.
            if not singletons:
                singletons.path = dir_name

            singletons.add(base_name)
            if entry and self.scan_options["stat"]:
                singletons.cache_stat(
                    base_name, entry.stat(follow_symlinks=True))

    def add_from_scan(self, file_entries):
        """Shortcut for adding file sequences from os/scandir.walk."""
        for file_entry in file_entries:
            self.add_file(file_entry)

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

    def scan_path(self, search_path, max_levels=-1, min_levels=-1):
        """Scan supplied path, add all discovered files to the instance."""
        search_path = search_path.rstrip(os.path.sep)
        search_seps = search_path.count(os.path.sep)

        for root, dir_entries, file_entries in self._scandir_walk(search_path):
            # Cheap and easy way to limit our search depth: count path
            # separators!
            cur_level = root.count(os.path.sep) - search_seps

            max_out = max_levels > -1 and cur_level == max_levels
            min_out = min_levels > -1 and cur_level <= min_levels

            if max_out:
                del dir_entries[:]
            if min_out:
                del file_entries[:]

            self.add_from_scan(file_entries)

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

    def _get_data(self, typ):
        """Return dictionary of the specified data type from the instance."""
        output = dict()
        for loc, data in self.locations.iteritems():
            if data[typ]:
                output[loc] = data[typ]

        return output

    def _scandir_walk(self, search_path, follow_symlinks=True):
        """Recursively yield DirEntry objects for given directory."""
        root, dir_entries, file_entries = search_path, list(), list()
        for entry in scandir(search_path):
            if entry.name.startswith(".") and not self.scan_options["all"]:
                continue
            if entry.is_dir(follow_symlinks=follow_symlinks):
                dir_entries.append(entry)
            elif entry.is_file(follow_symlinks=follow_symlinks):
                file_entries.append(entry)

        yield root, dir_entries, file_entries

        for entry in dir_entries:
            for data in self._scandir_walk(entry.path):
                yield data
