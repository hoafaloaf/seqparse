"""The main engine for the seqparse module."""

# Standard Libraries
import os
from collections import defaultdict

# Third Party Libraries
import six

from .containers import FileSequenceContainer, SingletonContainer
from .regex import SeqparseRegexMixin
from .sequences import FrameSequence

# Use the built-in version of scandir/walk if possible, otherwise use the
# scandir module version.
try:
    from os import scandir  # pylint: disable=W0611,C0412
except ImportError:  # pragma: no cover
    from scandir import scandir  # pylint: disable=W0611,C0412

__all__ = ("Seqparse", )

###############################################################################
# Class: Seqparse


class Seqparse(SeqparseRegexMixin):
    """
    Storage and parsing engine for file sequences.

    The primary usage for this class is to scan specified locations on disk for
    file sequences and singletons (any file that cannot be classified as a
    member of a file sequence).

    Examples:

        With the following file structure ...

            test_dir/
                TEST_DIR.0001.tif
                TEST_DIR.0002.tif
                TEST_DIR.0003.tif
                TEST_DIR.0004.tif
                TEST_DIR.0010.tif
                SINGLETON.jpg

        >>> from seqparse.seqparse import Seqparse
        >>> parser = Seqparse()
        >>> parser.scan_path("test_dir")
        >>> for item in parser.output():
        ...     print str(item)
        ...
        test_dir/TEST_DIR.0001-0004,0010.tif
        test_dir/SINGLETON.jpg
        >>> for item in parser.output(seqs_only=True):
        ...     print str(item)
        ...
        test_dir/TEST_DIR.0001-0004,0010.tif
        >>> for item in parser.output(missing=True):
        ...     print str(item)
        ...
        test_dir/TEST_DIR.0005-0009.tif
    """

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
        """
        Add a file to the parser instance.

        Args:
            file_name (str): The name of the file you'd like to add to the
                parser.

        Returns:
            None
        """
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

            if self.scan_options["stat"]:
                # "entry" *should* only ever be defined if it was passed in via
                # the scan_path method.
                if entry:
                    stat = entry.stat(follow_symlinks=True)
                else:
                    stat = os.stat(file_name)
                ext[pad].cache_stat(int(frames), stat)

        else:
            dir_name, base_name = os.path.split(file_name)
            loc = self.locations[dir_name]

            singletons = loc["files"]

            # Set the path properties at initialization.
            if not singletons:
                singletons.path = dir_name

            singletons.add(base_name)
            if self.scan_options["stat"]:
                if entry:
                    stat = entry.stat(follow_symlinks=True)
                else:
                    stat = os.stat(file_name)
                singletons.cache_stat(base_name, stat)

    def output(self, missing=False, seqs_only=False):
        """
        Yield a list of contained singletons and file sequences.

        Args:
            missing (bool, optional): Whether to yield "inverted" file
                sequences (ie, the missing files). Defaults to False. NOTE:
                Using this option implies that seqs_only == True.
            seqs_only (bool, optional): Whether to only yield file sequences
                (if any). Defaults to False.

        Yields:
            File and/or FileSequence instances, depending on input arguments.
        """
        if missing:
            seqs_only = True

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

    def scan_path(self, search_paths, max_levels=-1, min_levels=-1):
        """
        Scan supplied path, add all discovered files to the instance.

        Args:
            search_paths (str): The location(s) on disk you'd like to scan for
                file sequences and singletons.
            max_levels (int, optional): Descend at most the specified number (a
                non- negative integer) of directories below the starting point.
                max_levels == 0 means only scan the starting-point itself.
            min_levels (int, optional): Do not scan at levels less than
                specified number (a non-negative integer). min_levels == 1
                means scan all levels except the starting-point.

        Returns:
            None
        """
        if isinstance(search_paths, (list, set, tuple)):
            for search_path in search_paths:
                self.scan_path(search_path, max_levels=-1, min_levels=-1)
            return
        if os.path.isfile(search_paths):
            self.add_file(search_paths)
            return

        search_path = search_paths.rstrip(os.path.sep)
        search_seps = search_paths.count(os.path.sep)

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

            self._add_from_scan(file_entries)

    def _add_from_scan(self, file_entries):
        """
        Shortcut for adding file sequences from os/scandir.walk.

        Args:
            file_entries (iterable): Iterable (list-like object or generator)
                of scandir-style DirEntry instances for files discovered on
                disk.

        Returns:
            None
        """
        for file_entry in file_entries:
            self.add_file(file_entry)

    def _get_data(self, typ):
        """
        Return dictionary of the specified data type from the instance.

        Args:
            typ (str): "seqs" (for file sequences) or "files" (for singletons).

        Returns:
            dict of all data of the specified type, indexed by containing
            directory.
        """
        output = dict()
        for loc, data in six.iteritems(self.locations):
            if data[typ]:
                output[loc] = data[typ]

        return output

    def _scandir_walk(self, search_path, follow_symlinks=True):
        """
        Recursively yield DirEntry objects for given directory.

        Args:
            search_path (str): Directory to scan for files.
            follow_symlinks (bool, optional): Whether to follow symlinks
                dicovered at scan time. Defaults to False.

        Yields:
            DirEntry representations of discovered files.
        """
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

    @staticmethod
    def validate_frame_sequence(frame_seq):
        """
        Whether the supplied frame (not file) sequence is valid.

        Args:
            frame_seq (str): The string representation of the frame sequence
                to validate.

        Returns:
            None if the supplied sequence is invalid, a (possibly corrected)
            string file sequence if valid.

        Examples:
            >>> from seqparse.seqparse import Seqparse
            >>> parser = Seqparse()
            >>> print parser.validate_frame_sequence("0001-0001")
            0001
            >>> print parser.validate_frame_sequence("0001-")
            None
            >>> print parser.validate_frame_sequence("3,1,5,7")
            1-7x2
        """
        try:
            seq = FrameSequence(frame_seq)
        except ValueError:
            return None

        return str(seq)
