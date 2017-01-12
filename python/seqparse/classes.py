"""Classes utilized by the Seqparse class."""

# Standard Libraries
from collections import MutableMapping, MutableSet

__all__ = ("FileExtension", "FileSequence", "FrameSequence")

###############################################################################
# Class: FrameChunk


class FrameChunk(object):
    """Representative for chunks of frames in a FrameSequence."""

    def __init__(self, first, last=None, step=1, pad=1):
        """Initialise the instance."""
        self._data = dict(
            first=None, last=None, length=None, pad=int(pad), step=None)
        self._output = None

        self.set_frames(first, last, step)

    def __len__(self):
        """Return the length of the frame chunk."""
        return self._data["length"]

    def __repr__(self):
        """Pretty representation of the instance."""
        blurb = ("{name}(first={first}, last={last}, step={step}, "
                 "length={length}, pad={pad})")
        return blurb.format(name=type(self).__name__, **self._data)

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

    def set_frames(self, first, last=None, step=1):
        """Set and validate the first and last frames of the chunk."""
        if last is None:
            last = first

        first = int(first)
        last = int(last)

        if last < first:
            message = "Last frame is less than first frame: %d < %d"
            raise ValueError(message % (last, first))

        # Calculate the length and the real last frame of the chunk.
        step = max(1, int(step))
        bits = (last - first) / step
        last = first + bits * step
        step = min(last - first, step)

        # Calculate the string representation of the frame chunk.
        self._output = "%0*d" % (self.pad, first)
        if bits == 1:
            self._output += ",%0*d" % (self.pad, last)
        elif bits > 1:
            self._output += "-%0*d" % (self.pad, last)

        if step > 1:
            self._output += "x%d" % step

        self._data.update(first=first, last=last, length=(1 + bits), step=step)

        return self._output


###############################################################################
# Class: FrameSequence


class FrameSequence(MutableSet):
    """Representative for zero-padded frame sequences."""

    def __init__(self, pad=1, iterable=None):
        """Initialise the instance."""
        super(FrameSequence, self).__init__()

        self.__initialise()

        self.pad = pad

        for item in iterable or []:
            self.add(item)

    def __initialise(self):
        """Define initial attributes for the class."""
        self.__set = set()

        self._chunks = list()
        self._dirty = True
        self._output = None
        self._pad = 1

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        return int(item) in self.__set

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        return iter(self.__set)

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self.__set)

    def __repr__(self):
        """Pretty representation of the instance."""
        blurb = "%s(pad=%d, frames=set(%s))"
        return blurb % (type(self).__name__, self.pad, sorted(self.__set))

    def __str__(self):
        """String reprentation of the frame sequence."""
        if self.is_dirty:
            self.calculate()

        return self._output

    @property
    def is_dirty(self):
        """Whether the output needs to be recalculated after an update."""
        return self._dirty

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
            except:
                raise AttributeError("Invalid value specified (%s)" % item)

            len_item = len(item)
            if len_item < self.pad:
                message = "Specified value is incorrectly padded (%d < %d)"
                raise AttributeError(message % (len_item, self.pad))

        self.__set.add(int(item))
        self._dirty = True

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        self.__set.discard(item)
        self._dirty = True

    def update(self, iterable):
        """Defining item update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def calculate(self):
        """Calculate the output file sequence."""
        self._output = ""
        del self._chunks[:]

        num_frames = len(self)
        if not num_frames:
            return

        all_frames = sorted(self)

        if num_frames == 1:
            self._chunks.append(FrameChunk(all_frames[0]))

        else:
            current_frames = set()
            prev_step = 0
            for ii in xrange(num_frames - 1):
                frames = all_frames[ii:ii + 2]
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

        self._dirty = False

    def _chunk_from_frames(self, frames, step, pad):
        """Internal shortcut for creating FrameChunk from a list of frames."""
        frames = sorted(frames)
        return FrameChunk(frames[0], frames[-1], step, pad)


###############################################################################
# Class: FileParent


class FileParent(MutableMapping):
    """Base class for FileExtension and FileSequence classes."""

    _CHILD_CLASS = dict

    def __init__(self):
        """Initialise the instance."""
        super(FileParent, self).__init__()

    def __delitem__(self, key):
        """Define key deletion logic (per standard dictionary)."""
        del self.__dict__[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self.__dict__)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self.__dict__)


###############################################################################
# Class: FileExtensionn


class FileExtension(FileParent):
    """Container for frame sequences, indexed by zero-padding."""

    _CHILD_CLASS = FrameSequence

    def __init__(self):
        """Initialise the instance."""
        super(FileExtension, self).__init__()

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self.__dict__:
            self.__dict__[key] = self._CHILD_CLASS(pad=key)

        return self.__dict__[key]

    def __repr__(self):
        """Pretty representation of the instance."""
        blurb = ("{name}(pads={pads})")
        return blurb.format(name=type(self).__name__, pads=sorted(self))

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._CHILD_CLASS(value)

        if not isinstance(value, self._CHILD_CLASS) or value is None:
            raise ValueError

        self.__dict__[key] = value


###############################################################################
# Class: FileSequence


class FileSequence(FileParent):
    """Representative for file sequences, indexed by file extension."""

    _CHILD_CLASS = FileExtension

    def __init__(self):
        """Initialise the instance."""
        super(FileSequence, self).__init__()

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self.__dict__:
            self.__dict__[key] = self._CHILD_CLASS()

        return self.__dict__[key]

    def __repr__(self):
        """Pretty representation of the instance."""
        blurb = ("{name}(exts={exts})")
        return blurb.format(name=type(self).__name__, exts=sorted(self))

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._CHILD_CLASS(value)

        if not isinstance(value, self._CHILD_CLASS) or value is None:
            raise ValueError

        self.__dict__[key] = value
