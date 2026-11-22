"""The main engine for the seqparse module."""

from collections import defaultdict
import os

from .containers import FileSequenceContainer, SingletonContainer
from .regex import SeqparseRegexMixin
from .sequences import FrameSequence

__all__ = ("Seqparse",)


def _stat(file_name, entry=None):
    """
    Disk stats for a file, following symlinks.

    Args:
        file_name (str): Path to the file.
        entry (DirEntry, optional): The file's DirEntry when it was found via
            scan_path; its cached stat is used in preference to os.stat.

    Returns:
        stat_result for the file.
    """
    if entry:
        return entry.stat(follow_symlinks=True)
    return os.stat(file_name)


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
        super().__init__()

        self._locs = defaultdict(
            lambda: {
                "seqs": defaultdict(FileSequenceContainer),
                "files": SingletonContainer(),
            }
        )

        self._options = {"all": False, "stat": False}

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        num_seqs = len(list(self.output(seqs_only=True)))
        num_files = len(list(self.output())) - num_seqs

        blurb = "{name}(sequences={seqs}, singletons={files})"
        return blurb.format(
            name=type(self).__name__, files=num_files, seqs=num_seqs
        )

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
        on_disk = type(file_name).__name__ == "DirEntry"
        self._add_file(file_name, on_disk=on_disk)

    def _add_file(self, file_name, on_disk=False):
        """
        Add a file (or, for strings, a whole file sequence) to the instance.

        Args:
            file_name (str or DirEntry): The file to add.
            on_disk (bool, optional): Whether file_name is a single file that
                exists on disk (a DirEntry or a path found by scanning).

        Returns:
            None
        """
        entry = None
        if type(file_name).__name__ == "DirEntry":
            entry = file_name
            file_name = file_name.path

        dir_name, base_name = os.path.split(str(file_name))

        # A file found on disk is a single frame; a frame *sequence* in its
        # name (eg "foo.1-3.exr") is just part of a singleton's name. Strings
        # passed in directly may describe a whole sequence of files.
        if on_disk:
            sequence_bits = self.file_name_match(base_name)
            frames = sequence_bits.frame if sequence_bits else None
        else:
            sequence_bits = self.file_seq_match(base_name)
            frames = sequence_bits.frames if sequence_bits else None

        if sequence_bits:
            seq_name = sequence_bits.name or ""

            loc = self.locations[dir_name]
            sequence = loc["seqs"][seq_name]

            # Set the name and path properties at initialization.
            if not sequence:
                sequence.name = seq_name
                sequence.path = dir_name

            # We'll assume that a frame sequence is properly formed -- and use
            # the length of the first frame as the padding. The FrameSequence
            # to which we're adding the frames will do the actual validation.
            first_chunk = frames.lstrip(",").split(",")[0]
            pad = len(self.bits_match(first_chunk).first)

            ext = sequence[sequence_bits.ext]
            ext[pad].add(frames)

            # Disk stats only make sense for a single file (frame).
            if self.scan_options["stat"] and frames.isdigit():
                ext[pad].cache_stat(int(frames), _stat(file_name, entry))

        else:
            loc = self.locations[dir_name]

            singletons = loc["files"]

            # Set the path properties at initialization.
            if not singletons:
                singletons.path = dir_name

            singletons.add(base_name)
            if self.scan_options["stat"]:
                singletons.cache_stat(base_name, _stat(file_name, entry))

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
                    if not missing:
                        yield file_seq
                        continue
                    inverted = file_seq.invert()
                    # No gaps: nothing is missing.
                    if inverted:
                        yield inverted

            if seqs_only:
                continue

            yield from sorted(data["files"].output())

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
                self.scan_path(
                    search_path, max_levels=max_levels, min_levels=min_levels
                )
            return
        if os.path.isfile(search_paths):
            # Treat it exactly as a directory scan would treat the same file.
            self._add_file(search_paths, on_disk=True)
            return

        # Keep the root directory intact (stripping "/" would leave "").
        search_path = search_paths.rstrip(os.path.sep) or search_paths

        for cur_level, dir_entries, file_entries in self._scandir_walk(
            search_path
        ):
            max_out = max_levels > -1 and cur_level >= max_levels
            min_out = min_levels > -1 and cur_level < min_levels

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
        output = {}
        for loc, data in self.locations.items():
            if data[typ]:
                output[loc] = data[typ]

        return output

    def _scandir_walk(
        self,
        search_path,
        follow_symlinks=True,
        _level=0,
        _ancestors=frozenset(),
    ):
        """
        Recursively yield DirEntry objects for given directory.

        A directory that resolves to one of its own ancestors (a symlink loop)
        is skipped, as are subdirectories that cannot be read. Other symlinked
        directories are followed, so their files are reported under every path
        that reaches them (like `find -L`).

        Args:
            search_path (str): Directory to scan for files.
            follow_symlinks (bool, optional): Whether to follow symlinks
                dicovered at scan time. Defaults to True.

        Yields:
            tuple of (depth below the starting point, list of directory
            DirEntry instances, list of file DirEntry instances). Removing
            items from the directory list prevents descending into them.
        """
        real_path = os.path.realpath(search_path)
        if real_path in _ancestors:
            return
        _ancestors = _ancestors | {real_path}

        dir_entries, file_entries = [], []
        try:
            entries = list(os.scandir(search_path))
        except OSError:
            # Let errors on the starting point propagate to the caller.
            if not _level:
                raise
            return

        for entry in entries:
            if entry.name.startswith(".") and not self.scan_options["all"]:
                continue
            if entry.is_dir(follow_symlinks=follow_symlinks):
                dir_entries.append(entry)
            elif entry.is_file(follow_symlinks=follow_symlinks):
                file_entries.append(entry)

        yield _level, dir_entries, file_entries

        for entry in dir_entries:
            yield from self._scandir_walk(
                entry.path,
                follow_symlinks=follow_symlinks,
                _level=_level + 1,
                _ancestors=_ancestors,
            )

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
