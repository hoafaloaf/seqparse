"""Sequence-related data structures utilized by the Seqparse module."""

# Standard Libraries
import os
from collections import MutableSet

# Third Party Libraries
import six
from builtins import range

from .regex import SeqparseRegexMixin

__all__ = ("FileSequence", "FrameSequence", "SeqparsePadException")

###############################################################################
# Class: SeqparsePadException


class SeqparsePadException(Exception):
    """Exception thrown when unexpected frame padding is encountered."""

    def __init__(self, message):
        """
        Initialise the instance.

        Args:
            message (str): Error message to throw when exception is raised.
        """
        super(SeqparsePadException, self).__init__(message)


###############################################################################
# Class: FrameChunk


class FrameChunk(object):
    """
    Representative for chunks of frames in a FrameSequence.

    Args:
        first (int): First frame of the chunk.
        last (int, optional): Last frame of the chunk. Defaults to first
            frame if not specified.
        step (int, optional): Step size for the chunk. Defaults to 1.
        pad (int, optional): Frame padding for the chunk. Defaults to 1.
    """

    def __init__(self, first, last=None, step=1, pad=1):
        """Initialise the instance."""
        self._data = dict(
            first=None, last=None, length=None, pad=int(pad), step=None)
        self._output = None

        # This will calculate the string output as well!
        self.set_frames(first, last, step)

    def __contains__(self, item):
        """Whether the chunk contains the specified (non-)padded frame."""
        frame_num = int(item)
        for frame in range(self.first, self.last + 1, self.step):
            if frame < frame_num:
                continue
            elif frame_num == frame:
                if isinstance(item, six.string_types):
                    frame_len = len(item)
                    if item.startswith("0"):
                        return frame_len == self.pad
                    return frame_len >= self.pad
                return True

            return False

    def __eq__(self, other):
        """Define equality between instances."""
        if type(other) is type(self):
            return self._data == other._data  # pylint: disable=W0212
        return False

    def __iter__(self):
        """Iterate over the frames contained by the chunk."""
        for frame in range(self.first, self.last + 1, self.step):
            yield "{:0{}d}".format(frame, self.pad)

    def __len__(self):
        """Return the length of the frame chunk."""
        return self._data["length"] or 0

    def __ne__(self, other):
        """Define inequality between instance."""
        return not self.__eq__(other)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = ("{name}(first={first}, last={last}, step={step}, "
                 "length={length}, pad={pad})")
        return blurb.format(name=type(self).__name__, **self._data)

    def __reversed__(self):
        """Allow reversed iteration via reversed()."""
        return reversed(list(self))

    def __str__(self):
        """String representation of the frame chunk."""
        return self._output

    @property
    def first(self):
        """int: first frame of the chunk."""
        return self._data["first"]

    @property
    def last(self):
        """int: Last frame of the chunk."""
        return self._data["last"]

    @property
    def pad(self):
        """int: zero-padding for the frames contained by the object."""
        return self._data["pad"]

    @property
    def step(self):
        """int: step size for the frame chunk."""
        return max(self._data["step"] or 1, 1)

    def invert(self, first=None, last=None):
        """
        Calculate iterator for the frames missing from the chunk.

        Args:
            first (int, optional): First frame of the range that you'd like to
                invert. Defaults to first frame of the chunk if not specified.
            last (int, optional): Last frame of the range that you'd like to
                invert. Defaults to last frame of the chunk if not specified.

        Returns:
            FrameSequence instance containing the missing frames (if any).

        Examples:
            >>> from seqparse.sequences import FrameChunk
            >>> chunk = FrameChunk(first=5, last=11, step=2, pad=3)
            >>> print chunk
            005-011x2
            >>> inverted = chunk.invert()
            >>> print inverted
            006-010x2
            >>> print repr(inverted)
            FrameSequence(pad=3, frames=set([6, 8, 10]))
            >>> print chunk.invert(first=1)
            001-004,006-010x2
            >>> print chunk.invert(last=15)
            006-012x2,013-015
            >>> print chunk.invert(first=1, last=15)
            001-004,006-012x2,013-015
        """
        if first is None:
            first = self.first
        if last is None:
            last = self.last

        full_range = set(range(first, last + 1))
        return FrameSequence(full_range - set(map(int, self)), pad=self.pad)

    def set_frames(self, first, last=None, step=1):
        """
        Set and validate the first and last frames of the chunk.

        Args:
            first (int): First frame of the chunk.
            last (int, optional): Last frame of the chunk. Defaults to first
                frame if not specified.
            step (int, optional): Step size for the chunk. Defaults to 1.

        Returns:
            str representation of the frame chunk.
        """
        if last is None:
            last = first

        first = int(first)
        last = int(last)
        step = max(1, int(step or 1))

        if last < first:
            message = "Last frame is less than first frame: {:d} < {:d}"
            raise ValueError(message.format(last, first))

        # Calculate the length and the real last frame of the chunk.
        bits = (last - first) // step
        last = first + bits * step
        step = min(last - first, step)

        # Calculate the string representation of the frame chunk.
        self._output = "{:0{}d}".format(first, self.pad)
        if bits == 1:
            self._output += ",{:0{}d}".format(last, self.pad)
        elif bits > 1:
            self._output += "-{:0{}d}".format(last, self.pad)

        if step > 1 and bits > 1:
            self._output += "x{:d}".format(step)

        self._data.update(first=first, last=last, length=(1 + bits), step=step)
        return self._output


###############################################################################
# Class: FrameSequence


class FrameSequence(MutableSet, SeqparseRegexMixin):
    """
    Representative for zero-padded frame sequences.

    Args:
        frames (many types, optional): Initial frame range to store in the
            instance. Acceptable input types include FrameChunk, FrameSequence
            instances, string representation of a frame sequence, list, set, or
            tuple of integer frames.
        pad (int, optional): Initial zero-padding for the instance. Ignored
            if input iterable is a either a FrameChunk, FrameSequence, or
            string representation of a frame sequence.

    Examples:
        All of the following will result in equivalent output:

        >>> FrameSequence(range(1,6), pad=4)
        >>> FrameSequence(set([1, 2, 3, 4, 5]), pad=4)
        >>> FrameSequence("0001-0005")
        >>> FrameSequence(FrameChunk(first=1, last=5, pad=4))
    """

    def __init__(self, frames=None, pad=1):
        """Initialise the instance."""
        super(FrameSequence, self).__init__()

        self._attrs = dict(
            chunks=list(), dirty=True, is_padded=False, pad=None, stat=dict())

        self._data = set()
        self._output = None

        if isinstance(frames, six.string_types):
            if not self.is_frame_sequence(frames):
                blurb = "Invalid iterable specified ({}, {!r})"
                raise ValueError(blurb.format(type(frames), frames))
            self._add_frame_sequence(frames)
            return
        # NOTE: This could probably be made more efficient by copying a
        # FrameSequence's _data attribute and/or checking to see if _chunks
        # had anything in it. We shouldn't have to count on recalculating if
        # the job's already been done for us.
        elif isinstance(frames, (FrameChunk, FrameSequence)):
            pad = frames.pad
            '''
            if isinstance(frames, FrameSequence):
                self.stat().update(copy.deepcopy(frames.stat()))
            '''
        elif frames and not isinstance(frames, (list, tuple, set)):
            frames = [frames]

        self.pad = pad

        for item in frames or []:
            self.add(item)

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        if int(item) in self._data:
            if isinstance(item, six.string_types):
                item_pad = len(item)
                if item.startswith("0"):
                    return item_pad == self.pad
                else:
                    return item_pad >= self.pad

            return True

        return False

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        if self.is_dirty:
            self.calculate()

        for chunk in self._attrs["chunks"]:
            for frame in chunk:
                yield frame

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self._data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "{}(pad={:d}, frames=set({!r}))"
        return blurb.format(type(self).__name__, self.pad, sorted(self._data))

    def __reversed__(self):
        """Allow reversed iteration via reversed()."""
        return reversed(list(self))

    def __str__(self):
        """String reprentation of the frame sequence."""
        self.calculate()
        return self._output

    @property
    def is_dirty(self):
        """bool: Whether output needs to be recalculated after an update."""
        return self._attrs["dirty"]

    @property
    def is_padded(self):
        """bool: Whether the FrameSequence contains any zero-padded frames."""
        self.calculate()
        return self._attrs["is_padded"]

    @property
    def pad(self):
        """
        int: Zero-padding for the frames contained by the object.

        Minimum acceptable value for pad is 1.
        """
        return self._attrs["pad"]

    @pad.setter
    def pad(self, val):
        self._attrs["pad"] = max(1, int(val or 1))

    def add(self, item):
        """Defining item addition logic (per standard set)."""
        if isinstance(item, six.string_types):
            if self.is_frame_sequence(item):
                if not item.isdigit():
                    self._add_frame_sequence(item)
                    return
            else:
                raise ValueError("Invalid value specified ({!r})".format(item))

            item_pad = len(item)
            if item.startswith("0") and item_pad != self.pad:
                blurb = ("Specified value ({!r}) is incorrectly padded ({:d} "
                         "!= {:d})")
                raise SeqparsePadException(
                    blurb.format(item, item_pad, self.pad))

            self._data.add(int(item))

        elif isinstance(item, (list, set, tuple)):
            self._add_from_iterable(item)

        elif isinstance(item, (FrameChunk, FrameSequence)):
            if item.pad != self.pad:
                blurb = ("Specified value ({!r}) is incorrectly padded ({:d} "
                         "!= {:d})")
                raise SeqparsePadException(
                    blurb.format(item, item.pad, self.pad))
            self._add_from_iterable(item)

        else:
            self._data.add(int(item))

        self._attrs["dirty"] = True

    def _add_from_iterable(self, iterable):
        """
        Add items from supplied iterable to the instance.

        Args:
            iterable (many types): Iterable (usually a list-list object) from
                which you'd like to add items to the instance.

        Returns:
            None
        """
        for item in iterable:
            self.add(item)

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        if isinstance(item, six.string_types):
            if item.startswith("0"):
                item_pad = len(item)
                if item_pad != self.pad:
                    blurb = ("Specified value ({!r}) is incorrectly padded "
                             "({:d} != {:d}))")
                    raise SeqparsePadException(
                        blurb.format(item, item_pad, self.pad))

            item = int(item)

        self._data.discard(item)
        self._attrs["dirty"] = True

    def update(self, iterable):
        """Defining item update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def calculate(self, force=False):
        """
        Calculate the output file sequence.

        Output string file sequence will always be recalculated if the instance
        has been marked as "dirty" when its contents have been modified by an
        external process.

        Args:
            force (bool, optional): Whether to force recalculation.

        Returns:
            None
        """
        if not (self.is_dirty or force):
            return

        self._attrs["is_padded"] = False
        del self._attrs["chunks"][:]
        self._output = ""

        num_frames = len(self._data)
        if not num_frames:
            return

        all_frames = sorted(self._data)
        if num_frames == 1:
            self._attrs["chunks"].append(
                FrameChunk(all_frames[0], pad=self.pad))

        else:
            current_frames = set()
            prev_step = 0
            for index in range(num_frames - 1):
                frames = all_frames[index:index + 2]
                step = frames[1] - frames[0]

                if not prev_step:
                    prev_step = step

                if prev_step != step:
                    chunk = self._chunk_from_frames(current_frames, prev_step,
                                                    self.pad)
                    self._attrs["chunks"].append(chunk)
                    prev_step = 0
                    current_frames = set([frames[1]])

                else:
                    current_frames.update(frames)

            if current_frames:
                chunk = self._chunk_from_frames(current_frames, step, self.pad)
                self._attrs["chunks"].append(chunk)

        # This will be used by the parent FileExtension instance during the
        # zero-pad consolidation stage of the output process.
        self._attrs["is_padded"] = all_frames[0] < 10**(self.pad - 1)

        # Optimize padding in cases similar to 1, 2, 1000.
        self._output = ",".join(str(x) for x in self._attrs["chunks"])

        self._attrs["dirty"] = False

    def invert(self):
        """
        Calculate frames missing from the sequence.

        Returns:
            FrameSequence containing the missing frames (if any).
        """
        self.calculate()
        inverted = FrameSequence(pad=self.pad)
        num_chunks = len(self._attrs["chunks"])

        if num_chunks == 1:
            inverted.add(self._attrs["chunks"][0].invert())

        elif num_chunks:
            for index in range(num_chunks - 1):
                current_chunk = self._attrs["chunks"][index]
                next_chunk = self._attrs["chunks"][index + 1]
                inverted.add(current_chunk.invert(last=next_chunk.first - 1))

            inverted.add(self._attrs["chunks"][-1].invert())

        return inverted

    def _add_frame_sequence(self, frame_seq):
        """
        Add a string frame sequence to the instance.

        Args:
            frame_seq (str): frame sequence that you'd like to add to the
                instance.

        Returns:
            None
        """
        for bit in frame_seq.split(","):
            if not bit:
                continue

            first, last, step = self.bits_match(bit)
            pad = len(first)
            if self.pad is None:
                self.pad = pad

            self.add(FrameChunk(first, last, step, pad))

    @staticmethod
    def _chunk_from_frames(frames, step, pad):
        """
        Calculate FrameChunk from a list of frames.

        Args:
            frames (list of int): (first, last) frames used to initialise the
                output FrameChunk instance.
            step (int): Frame step size.
            pad (int): Zero-padding for the output FrameChunk.

        Returns:
            FrameChunk containing the input frames.
        """
        frames = sorted(frames)
        return FrameChunk(frames[0], frames[-1], step, pad)


###############################################################################
# Class: FileSequence


class FileSequence(FrameSequence):  # pylint: disable=too-many-ancestors
    """
    Representative for sequences of files.

    You may create a new instance of this class a couple of ways:

    1. Either clone a new instance from an existing one ...

        >>> clone = FileSequence(parent)

    2. ... or create a valid instance by providing a file extension and at
       least one frame (the base name is optional in every sense of the word):

       >>> fseq = FileSequence(frames="0001", ext="exr")

    Args:
        name (str, optional): Base name (including containing directory) for
            the file sequence.
        frames (many types, optional): Initial frame range to store in the
            instance. Acceptable input types include FrameChunk, FrameSequence
            instances, string representation of a frame sequence, list, set, or
            tuple of integer frames.
        ext (str, optional): File extension for the sequence.
        pad (int, optional): Frame padding for the sequence. Defaults to 1.
    """

    def __init__(self, name=None, frames=None, ext=None, pad=1):
        """Initialise the instance."""
        self._cache = dict(ctime=None, mtime=None, size=None)
        self._info = dict(ext=None, full=None, name=None, path=None)
        self._stat = dict()

        if name:
            if isinstance(name, six.string_types):
                file_seq_bits = self.file_seq_match(name)
                if file_seq_bits:
                    name, frames, ext = file_seq_bits
                    pad = None

            elif isinstance(name, FileSequence):
                name, frames, ext, pad = (name.full_name, name.pretty_frames,
                                          name.ext, name.pad)
        if frames is None:
            frames = list()

        super(FileSequence, self).__init__(frames, pad=pad)

        self.ext = ext
        self.name = name

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        if str(item).isdigit():
            return super(FileSequence, self).__contains__(item)
        return item in set(self)

    def __eq__(self, other):
        """Define equality between instances."""
        if type(other) is type(self):
            return super(FileSequence, self).__eq__(other)
        return False

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        for frame in super(FileSequence, self).__iter__():
            yield self._get_sequence_output(frame)

    def __ne__(self, other):
        """Define inequality between instance."""
        return not self.__eq__(other)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = ("{cls}(full_name={full!r}, ext={ext!r}, pad={pad}, "
                 "frames=set({fr!r}))")
        return blurb.format(
            cls=type(self).__name__,
            fr=sorted(self._data),
            pad=self.pad,
            **self._info)

    def __str__(self):
        """String reprentation of the frame sequence."""
        frames = super(FileSequence, self).__str__()
        return self._get_sequence_output(frames)

    @property
    def ctime(self):
        """
        int: Most recent inode or file change time for a file in the sequence.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._cache["ctime"]

    @property
    def ext(self):
        """str: File extension for the sequence."""
        return self._info["ext"]

    @ext.setter
    def ext(self, val):
        self._info["ext"] = None
        if val:
            self._info["ext"] = str(val)

    @property
    def frames(self):
        """iterator(str): the file sequence's padded frames."""
        for frame in super(FileSequence, self).__iter__():
            yield frame

    @property
    def pretty_frames(self):
        """str: pretty representation of the file sequence's print frames."""
        return super(FileSequence, self).__str__()

    @property
    def full_name(self):
        """str: Full name of the sequence, including containing directory."""
        return self._info["full"]

    @property
    def mtime(self):
        """
        int: Most recent file modification time for a file in the sequence.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._cache["mtime"]

    @property
    def name(self):
        """
        str: Base name of the file sequence (no containing directory).

        Note: Setting this property will modify both the `full_path` and `path`
        properties.
        """
        return self._info["name"]

    @name.setter
    def name(self, val):
        self._info["name"] = None
        if val:
            val = str(val)

            # If it's a file path (complete with directory prefix), set the
            # path property as well.
            if os.sep in val:
                path_name, val = os.path.split(os.path.normpath(val))
                self.path = path_name
            self._info["name"] = val

        self._info["full"] = os.path.join(self._info["path"] or "", val or "")

    @property
    def path(self):
        """
        str: Directory in which the contained files are located.

        Note: Setting the `name` property will reset the contained value.
        """
        return self._info["path"]

    @path.setter
    def path(self, val):
        self._info["path"] = None
        if val:
            self._info["path"] = str(os.path.normpath(val))

        self._info["full"] = os.path.join(val or "", self._info["name"] or "")

    @property
    def size(self):
        """
        int: Total size of the file sequence in bytes.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._cache["size"]

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        super(FileSequence, self).discard(item)
        self._stat.pop(item, None)

    def update(self, other):
        """Defining item update logic (per standard set)."""
        if isinstance(other, FileSequence):
            for attr in ("ext", "full_name"):
                other_value = getattr(other, attr)
                self_value = getattr(self, attr)
                if other_value != self_value:
                    blurb = ("Attribute mismatch on supplied FileSequence "
                             "instance ({}): self:{!r} != other:{!r}")
                    raise ValueError(
                        blurb.format(attr, self_value, other_value))

            self.stat().update(other.stat())
            other = other.frames

        for item in other:
            self.add(item)

    def cache_stat(self, frame, input_stat):
        """
        Cache file system stat data for the specified frame.

        Input disk stat value will be stored in a new stat_result
        instance.

        Args:
            frame (int): Frame for which you'd like to cache the supplied stat
                data.
            input_stat (stat_result): Value that you'd like to cache.

        Returns:
            stat_result that was successfully cached.
        """
        from . import get_stat_result

        frame = int(frame)
        self._stat[frame] = get_stat_result(input_stat)
        return self._stat[frame]

    def calculate(self, force=False):
        """
        Calculate the output file sequence.

        Output string file sequence will always be recalculated if the instance
        has been marked as "dirty" when its contents have been modified by an
        external process.

        Args:
            force (bool, optional): Whether to force recalculation.

        Returns:
            None
        """
        if not (self.is_dirty or force):
            return

        super(FileSequence, self).calculate(force=force)

        # Cache disk stats for easy/quick access via property ...
        self._aggregate_stats()

    def invert(self):
        """
        Calculate file names missing from the sequence.

        Returns:
            FileSequence containing the missing files (if any).
        """
        frames = super(FileSequence, self).invert()
        inverted = FileSequence(
            name=self.full_name, frames=frames, ext=self.ext)
        return inverted

    def stat(self, frame=None, force=False, lazy=False):
        """
        Individual frame file system status.

        Args:
            frame (int, optional): Frame for which you'd like to return the
                disk stats.
            force (bool, optional): Whether to force disk stat query,
                regardless of caching status.
            lazy (bool, optional): Whether to query disk stats should no cached
                value exist.

        Returns:
            None if a frame has been specified but disk stats have not been
            cached.
            stat_result if a frame has been specified and disk stats have
            been previously cached.
            dict of disk stats, indexed by int frame if no frame has been
            specified.
        """
        if frame is None:
            if force or lazy:
                raise ValueError(
                    "Must specify frame when querying for file disk stats.")

        elif force or (lazy and self._stat.get(frame) is None):
            file_name = self._get_sequence_output(frame)
            self.cache_stat(frame, os.stat(file_name))

        if frame is None:
            return self._stat
        return self._stat.get(int(frame), None)

    def _aggregate_stats(self):
        """
        Aggregate stats for a variety of file sequence properties.

        This method clears all cached aggregate values before recalculating
        new values.

        Returns:
            None
        """
        self._cache = dict(ctime=None, mtime=None, size=None)
        if not self.stat():
            return self._cache

        ctime = mtime = size = 0

        # Disabling pylint here because the stat object will never be a
        # dict at this point ... unless somebody's been messing with the data
        # cache directly.
        for frame in self._data:
            stat = self.stat(frame)
            ctime = max(ctime, stat.st_ctime)  # pylint: disable=E1101
            mtime = max(mtime, stat.st_mtime)  # pylint: disable=E1101
            size += stat.st_size  # pylint: disable=E1101

        self._cache = dict(ctime=ctime, mtime=mtime, size=size)

    def _get_sequence_output(self, frames):
        """
        Calculate a valid file sequence string from the given iterator.

        Args:
            frames (str): String representation of a frame sequence.

        Returns:
            str representation of a file sequence.
        """
        if not frames:
            return ""
        elif str(frames).isdigit():
            frames = "{:0{}d}".format(int(frames), self.pad)
        elif not self.ext:
            raise AttributeError(
                "File sequence extension has not been defined.")

        file_name = "{fr}.{ext}"
        if self.name:
            file_name = "{name}.{fr}.{ext}"

        file_name = file_name.format(fr=frames, **self._info)
        return os.path.join(self.path or "", file_name)
