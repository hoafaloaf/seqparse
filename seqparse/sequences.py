"""Sequence-related data structures utilized by the Seqparse module."""

# Standard Libraries
import copy
import os
from collections import MutableSet

from .regex import SeqparseRegexMixin

__all__ = ("FrameSequence", "SeqparsePadException")

###############################################################################
# Class: SeqparsePadException


class SeqparsePadException(Exception):
    """Exception thrown when unexpected frame padding is encountered."""

    def __init__(self, message):
        """Initialise the instance."""
        super(SeqparsePadException, self).__init__(message)


###############################################################################
# Class: FrameChunk


class FrameChunk(object):
    """Representative for chunks of frames in a FrameSequence."""

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
        for frame in xrange(self.first, self.last + 1, self.step):
            if frame < frame_num:
                continue
            elif frame_num == frame:
                if isinstance(item, basestring):
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
        for frame in xrange(self.first, self.last + 1, self.step):
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
        """The first frame of the chunk."""
        return self._data["first"]

    @property
    def last(self):
        """The last frame of the chunk."""
        return self._data["last"]

    @property
    def pad(self):
        """Integer zero-padding for the frames contained by the object."""
        return self._data["pad"]

    @property
    def step(self):
        """Integer step size for the frame chunk."""
        return max(self._data["step"] or 1, 1)

    def invert(self):
        """Return an iterator for the frames missing from the chunk."""
        full_range = set(xrange(self.first, self.last + 1))
        return FrameSequence(full_range - set(map(int, self)), pad=self.pad)

    def set_frames(self, first, last=None, step=1):
        """Set and validate the first and last frames of the chunk."""
        if last is None:
            last = first

        first = int(first)
        last = int(last)
        step = max(1, int(step or 1))

        if last < first:
            message = "Last frame is less than first frame: {:d} < {:d}"
            raise ValueError(message.format(last, first))

        # Calculate the length and the real last frame of the chunk.
        bits = (last - first) / step
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
    """Representative for zero-padded frame sequences."""

    def __init__(self, iterable=None, pad=1):
        """Initialise the instance."""
        super(FrameSequence, self).__init__()

        self._attrs = dict(
            chunks=list(), dirty=True, is_padded=False, pad=None, stat=dict())

        self._data = set()
        self._cache = dict(ctime=None, mtime=None, size=None)
        self._output = None

        # NOTE: This could probably be made more efficient by copying a
        # FrameSequence's _data attribute and/or checking to see if _chunks
        # had anything in it. We shouldn't have to count on recalculating if
        # the job's already been done for us.
        if isinstance(iterable, (FrameChunk, FrameSequence)):
            pad = iterable.pad
            if isinstance(iterable, FrameSequence):
                self.stat.update(copy.deepcopy(iterable.stat))
        elif isinstance(iterable, basestring):
            if not self.is_frame_sequence(iterable):
                blurb = "Invalid iterable specified ({}, {!r})"
                raise ValueError(blurb.format(type(iterable), iterable))
            self._add_frame_sequence(iterable)
            return
        elif iterable and not isinstance(iterable, (list, tuple, set)):
            iterable = [iterable]

        self.pad = pad

        for item in iterable or []:
            self.add(item)

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        if int(item) in self._data:
            if isinstance(item, basestring):
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
    def ctime(self):
        """
        The most recent inode or file change time for a file in the sequence.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._cache["mtime"]

    @property
    def is_dirty(self):
        """Whether the output needs to be recalculated after an update."""
        return self._attrs["dirty"]

    @property
    def is_padded(self):
        """Return whether the FrameSequence contains any zero-padded frames."""
        self.calculate()
        return self._attrs["is_padded"]

    @property
    def mtime(self):
        """
        The most recent file modification time for a file in the sequence.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._cache["mtime"]

    @property
    def pad(self):
        """Integer zero-padding for the frames contained by the object."""
        return self._attrs["pad"]

    @pad.setter
    def pad(self, val):
        self._attrs["pad"] = max(1, int(val or 1))

    @property
    def size(self):
        """
        The total size of the file sequence in bytes.

        Returns None if the files have not been stat'd on disk.
        """
        self.calculate()
        return self._cache["size"]

    @property
    def stat(self):
        """Indiviual frame file system status, indexed by integer frame."""
        return self._attrs["stat"]

    def add(self, item):
        """Defining item addition logic (per standard set)."""
        if isinstance(item, basestring):
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
            map(self.add, item)

        elif isinstance(item, (FrameChunk, FrameSequence)):
            if item.pad != self.pad:
                blurb = ("Specified value ({!r}) is incorrectly padded ({:d} "
                         "!= {:d})")
                raise SeqparsePadException(
                    blurb.format(item, item.pad, self.pad))
            map(self.add, item)

        else:
            self._data.add(int(item))

        self._attrs["dirty"] = True

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        if isinstance(item, basestring):
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
        self._attrs["stat"].pop(item, None)

    def update(self, iterable):
        """Defining item update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def calculate(self, force=False):
        """Calculate the output file sequence."""
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
            for index in xrange(num_frames - 1):
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

        # Cache disk stats for easy/quick access via property ...
        self._cache_disk_stats()

        self._attrs["dirty"] = False

    def invert(self):
        """Return a FrameSequence of frames missing from the sequence."""
        self.calculate()
        inverted = FrameSequence(pad=self.pad)
        for chunk in self._attrs["chunks"]:
            inverted.add(chunk.invert())

        return inverted

    def _add_frame_sequence(self, frame_seq):
        """Add a string frame sequence to the instance."""
        for bit in frame_seq.split(","):
            if not bit:
                continue

            first, last, step = self.bits_match(bit)
            pad = len(first)
            if self.pad is None:
                self.pad = pad

            self.add(FrameChunk(first, last, step, pad))

    def _cache_disk_stats(self):
        """Cache disk stats for a variety of file sequence properties."""
        self._cache = dict(ctime=None, mtime=None, size=None)
        if not self.stat:
            return self._cache

        ctime = mtime = size = 0
        for frame in self._data:
            stat = self.stat.get(frame, dict())
            ctime = max(ctime, stat.get("ctime", 0))
            mtime = max(mtime, stat.get("mtime", 0))
            size += stat.get("size", 0)

        self._cache = dict(ctime=ctime, mtime=mtime, size=size)

    @staticmethod
    def _chunk_from_frames(frames, step, pad):
        """Internal shortcut for creating FrameChunk from a list of frames."""
        frames = sorted(frames)
        return FrameChunk(frames[0], frames[-1], step, pad)


###############################################################################
# Class: FileSequence


class FileSequence(FrameSequence):  # pylint: disable=too-many-ancestors
    """Representative for sequences of files."""

    def __init__(self, name=None, frames=None, ext=None, pad=1):
        """Initialise the instance."""
        self._info = dict(ext=None, full=None, name=None, path=None)

        if name:
            name_bits = self.file_seq_match(name)
            if name_bits:
                name, frames, ext = name_bits
                pad = None

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
    def ext(self):
        """The file extension for the sequence."""
        return self._info["ext"]

    @ext.setter
    def ext(self, val):
        self._info["ext"] = None
        if val:
            self._info["ext"] = str(val)

    @property
    def full_name(self):
        """The full (base) name of the file sequence."""
        return self._info["full"]

    @property
    def name(self):
        """The (base) name of the file sequence."""
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
        """Directory in which the contained files are located."""
        return self._info["path"]

    @path.setter
    def path(self, val):
        self._info["path"] = None
        if val:
            self._info["path"] = str(os.path.normpath(val))

        self._info["full"] = os.path.join(val or "", self._info["name"] or "")

    def invert(self):
        """Return a FileSequence of files missing from the sequence."""
        frames = super(FileSequence, self).invert()
        inverted = FileSequence(
            name=self.full_name, frames=frames, ext=self.ext)
        return inverted

    def _get_sequence_output(self, frames):
        """Return a valid file sequence string from the given iterator."""
        if not frames:
            return ""
        elif not self.ext:
            raise AttributeError(
                "File sequence extension has not been defined.")

        file_name = "{fr}.{ext}"
        if self.name:
            file_name = "{name}.{fr}.{ext}"

        file_name = file_name.format(fr=frames, **self._info)
        return os.path.join(self.path or "", file_name)
