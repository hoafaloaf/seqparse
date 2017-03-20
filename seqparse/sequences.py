"""Sequence-related data structures utilized by the Seqparse module."""

# Standard Libraries
import os
from collections import MutableSet

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

    def __iter__(self):
        """Iterate over the frames contained by the chunk."""
        for frame in xrange(self.first, self.last + 1, self.step):
            yield "%0*d" % (self.pad, frame)

    def __len__(self):
        """Return the length of the frame chunk."""
        return self._data["length"] or 0

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
            message = "Last frame is less than first frame: %d < %d"
            raise ValueError(message % (last, first))

        # Calculate the length and the real last frame of the chunk.
        bits = (last - first) / step
        last = first + bits * step
        step = min(last - first, step)

        # Calculate the string representation of the frame chunk.
        self._output = "%0*d" % (self.pad, first)
        if bits == 1:
            self._output += ",%0*d" % (self.pad, last)
        elif bits > 1:
            self._output += "-%0*d" % (self.pad, last)

        if step > 1 and bits > 1:
            self._output += "x%d" % step

        self._data.update(first=first, last=last, length=(1 + bits), step=step)
        return self._output


###############################################################################
# Class: FrameSequence


class FrameSequence(MutableSet):
    """Representative for zero-padded frame sequences."""

    def __init__(self, iterable=None, pad=1):
        """Initialise the instance."""
        self._data = set()

        self._chunks = list()
        self._dirty = True
        self._output = None
        self._pad = 1
        self._is_padded = False

        if isinstance(iterable, (FrameChunk, FrameSequence)):
            pad = iterable.pad
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

        for chunk in self._chunks:
            for frame in chunk:
                yield frame

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self._data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "%s(pad=%d, frames=set(%s))"
        return blurb % (type(self).__name__, self.pad, sorted(self._data))

    def __reversed__(self):
        """Allow reversed iteration via reversed()."""
        return reversed(list(self))

    def __str__(self):
        """String reprentation of the frame sequence."""
        if self.is_dirty:
            self.calculate()
            self._dirty = False
        return self._output

    @property
    def is_dirty(self):
        """Whether the output needs to be recalculated after an update."""
        return self._dirty

    @property
    def is_padded(self):
        """Return whether the FrameSequence contains any zero-padded frames."""
        if self.is_dirty:
            self.calculate()
        return self._is_padded

    @property
    def pad(self):
        """Integer zero-padding for the frames contained by the object."""
        return self._pad

    @pad.setter
    def pad(self, val):
        self._pad = max(1, int(val or 1))

    def add(self, item):
        """Defining item addition logic (per standard set)."""
        if isinstance(item, basestring):
            try:
                int(item)
            except ValueError:
                raise ValueError("Invalid value specified (%r)" % item)

            item_pad = len(item)
            if item.startswith("0") and item_pad != self.pad:
                blurb = "Specified value (%r) is incorrectly padded (%d != %d)"
                raise SeqparsePadException(blurb % (item, item_pad, self.pad))

            self._data.add(int(item))

        elif isinstance(item, (list, set, tuple)):
            map(self.add, item)

        elif isinstance(item, (FrameChunk, FrameSequence)):
            if item.pad != self.pad:
                blurb = "Specified value (%r) is incorrectly padded (%d != %d)"
                raise SeqparsePadException(blurb % (item, item.pad, self.pad))
            map(self.add, item)

        else:
            self._data.add(int(item))

        self._dirty = True

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        if isinstance(item, basestring):
            if item.startswith("0"):
                item_pad = len(item)
                if item_pad != self.pad:
                    blurb = ("Specified value (%r) is incorrectly padded "
                             "(%d != %d))")
                    raise SeqparsePadException(blurb %
                                               (item, item_pad, self.pad))

            item = int(item)

        self._data.discard(item)
        self._dirty = True

    def update(self, iterable):
        """Defining item update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def calculate(self):
        """Calculate the output file sequence."""
        self._is_padded = False
        self._output = ""
        del self._chunks[:]

        num_frames = len(self._data)
        if not num_frames:
            return

        all_frames = sorted(self._data)
        if num_frames == 1:
            self._chunks.append(FrameChunk(all_frames[0], pad=self.pad))

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
                    self._chunks.append(chunk)
                    prev_step = 0
                    current_frames = set([frames[1]])

                else:
                    current_frames.update(frames)

            if current_frames:
                chunk = self._chunk_from_frames(current_frames, step, self.pad)
                self._chunks.append(chunk)

        # This will be used by the parent FileExtension instance during the
        # zero-pad consolidation stage of the output process.
        self._is_padded = all_frames[0] < 10**(self.pad - 1)

        # Optimize padding in cases similar to 1, 2, 1000.
        self._output = ",".join(str(x) for x in self._chunks)
        self._dirty = False

    def invert(self):
        """Return a FrameSequence of frames missing from the sequence."""
        if self.is_dirty:
            self.calculate()

        inverted = FrameSequence(pad=self.pad)
        for chunk in self._chunks:
            inverted.add(chunk.invert())

        return inverted

    @staticmethod
    def _chunk_from_frames(frames, step, pad):
        """Internal shortcut for creating FrameChunk from a list of frames."""
        frames = sorted(frames)
        return FrameChunk(frames[0], frames[-1], step, pad)


###############################################################################
# Class: FileSequence


class FileSequence(FrameSequence):
    """Representative for sequences of files."""

    def __init__(self, name=None, ext=None, frames=None, pad=1):
        """Initialise the instance."""
        if frames is None:
            frames = list()

        super(FileSequence, self).__init__(frames, pad=pad)
        self._info = dict(ext=None, name=None, path=None)

        self.ext = ext
        self.name = name

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        if str(item).isdigit():
            return super(FileSequence, self).__contains__(item)
        return item in set(self)

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        for frame in super(FileSequence, self).__iter__():
            yield self._get_sequence_output(frame)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = ("{cls}(name={name!r}, ext={ext!r}, pad={pad}, "
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

    @property
    def path(self):
        """Directory in which the contained files are located."""
        return self._info["path"]

    @path.setter
    def path(self, val):
        self._info["path"] = None
        if val:
            self._info["path"] = str(os.path.normpath(val))

    def invert(self):
        """Return a FileSequence of files missing from the sequence."""
        frames = super(FileSequence, self).invert()
        return self._get_sequence_output(frames)

    def _get_sequence_output(self, frames):
        """Return a valid file sequence string from the given iterator."""
        if not frames:
            return ""

        file_name = "{fr}.{ext}"
        if self.name:
            file_name = "{name}.{fr}.{ext}"

        file_name = file_name.format(fr=frames, **self._info)
        return os.path.join(self.path or "", file_name)
