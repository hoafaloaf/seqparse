"""Classes utilized by the Seqparse class."""

# Standard Libraries
import os
from collections import MutableMapping, MutableSet

__all__ = ("FileExtension", "FileSequence", "FrameSequence", "Singletons")

###############################################################################
# Class: FrameChunk


class FrameChunk(object):
    """Representative for chunks of frames in a FrameSequence."""

    def __init__(self, first, last=None, step=1, pad=1):
        """Initialise the instance."""
        self.__data = dict(
            first=None, last=None, length=None, pad=int(pad), step=None)
        self._output = None

        # This will calculate the string output as well!
        self.set_frames(first, last, step)

    def __len__(self):
        """Return the length of the frame chunk."""
        return self.__data["length"] or 0

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = ("{name}(first={first}, last={last}, step={step}, "
                 "length={length}, pad={pad})")
        return blurb.format(name=type(self).__name__, **self.__data)

    def __str__(self):
        """String representation of the frame chunk."""
        return self._output

    @property
    def first(self):
        """The first frame of the chunk."""
        return self.__data["first"]

    @property
    def last(self):
        """The last frame of the chunk."""
        return self.__data["last"]

    @property
    def pad(self):
        """Integer zero-padding for the frames contained by the object."""
        return self.__data["pad"]

    @property
    def step(self):
        """Integer step size for the frame chunk."""
        return max(self.__data["step"] or 1, 1)

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

        self.__data.update(
            first=first, last=last, length=(1 + bits), step=step)
        return self._output


###############################################################################
# Class: FrameSequence


class FrameSequence(MutableSet):
    """Representative for zero-padded frame sequences."""

    def __init__(self, pad=1, iterable=None):
        """Initialise the instance."""
        self.__data = set()

        self._chunks = list()
        self._dirty = True
        self._output = None
        self._pad = 1
        self._is_padded = False

        self.pad = pad

        for item in iterable or []:
            self.add(item)

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        return int(item) in self.__data

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        return iter(self.__data)

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self.__data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "%s(pad=%d, frames=set(%s))"
        return blurb % (type(self).__name__, self.pad, sorted(self.__data))

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
            except AttributeError:
                raise AttributeError("Invalid value specified (%s)" % item)

            len_item = len(item)
            if len_item < self.pad:
                message = "Specified value is incorrectly padded (%d < %d)"
                raise AttributeError(message % (len_item, self.pad))

        self.__data.add(int(item))
        self._dirty = True

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        self.__data.discard(item)
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

        num_frames = len(self)
        if not num_frames:
            return

        all_frames = sorted(self)
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

    @staticmethod
    def _chunk_from_frames(frames, step, pad):
        """Internal shortcut for creating FrameChunk from a list of frames."""
        frames = sorted(frames)
        return FrameChunk(frames[0], frames[-1], step, pad)


###############################################################################
# Class: FileExtensionn


class FileExtension(MutableMapping):
    """Container for frame sequences, indexed by zero-padding."""

    _CHILD_CLASS = FrameSequence

    def __init__(self, name=None):
        """Initialise the instance."""
        self.__data = dict()
        self._name = None

        self.name = name

    def __delitem__(self, key):
        """Define key deletion logic (per standard dictionary)."""
        del self.__data[key]

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self.__data:
            self.__data[key] = self._CHILD_CLASS(pad=key)
        return self.__data[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self.__data)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self.__data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "{name}(pads={pads})"
        return blurb.format(name=type(self).__name__, pads=sorted(self))

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._CHILD_CLASS(value)
        if not isinstance(value, self._CHILD_CLASS) or value is None:
            raise ValueError

        self.__data[key] = value

    @property
    def name(self):
        """The (base) name of the file sequence."""
        return self._name

    @name.setter
    def name(self, val):
        self._name = None
        if val:
            self._name = str(val)

    def output(self):
        """Return a formatted list of all contained file extentions."""
        # First, check to see if we need to consolidate our frame sequences.
        data = sorted(self.items(), reverse=True)
        while len(data) > 1:
            pad, frames = data.pop(0)

            # NOTE: the is_padded() method will force recalculation if the
            # object is dirty.
            if not frames.is_padded:
                # TODO: prev_pad is unused, but leaving here for reference.
                # prev_pad, prev_frames = data[0]
                prev_frames = data[0][1]
                prev_frames.update(frames)
                del self[pad]

        for pad, frames in sorted(self.items()):
            yield str(frames)


###############################################################################
# Class: FileSequence


class FileSequence(MutableMapping):
    """Representative for file sequences, indexed by file extension."""

    _CHILD_CLASS = FileExtension

    def __init__(self, name=None, file_path=None):
        """Initialise the instance."""
        self.__data = dict()

        self._name = None
        self._path = None

        self.name = name
        self.path = file_path

    def __delitem__(self, key):
        """Define key deletion logic (per standard dictionary)."""
        del self.__data[key]

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self.__data:
            self.__data[key] = self._CHILD_CLASS(name=key)

        return self.__data[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self.__data)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self.__data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = ("{name}(path='{path}', exts={exts})")
        return blurb.format(
            name=type(self).__name__, exts=sorted(self), path=self.path)

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._CHILD_CLASS(value)

        if not isinstance(value, self._CHILD_CLASS) or value is None:
            raise ValueError

        self.__data[key] = value

    @property
    def name(self):
        """The (base) name of the file sequence."""
        return self._name

    @name.setter
    def name(self, val):
        self._name = None
        if val:
            self._name = str(val)

    @property
    def path(self):
        """Directory in which the contained files are located."""
        return self._path

    @path.setter
    def path(self, val):
        self._path = str(val or "")

    def output(self):
        """Return a formatted list of all contained file sequences."""
        for ext, data in sorted(self.items()):
            for output in data.output():
                if self.name:
                    bits = (self.name, output, ext)
                else:
                    bits = (output, ext)
                yield os.path.join(self.path, ".".join(bits))


###############################################################################
# class: Singletons


class Singletons(MutableSet):
    """Representative for singleton files."""

    def __init__(self, iterable=None, file_path=None):
        """Initialise the instance."""
        self.__data = set()

        self._path = None

        for item in iterable or []:
            self.add(item)

        self.path = file_path

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        return str(item) in self.__data

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        return iter(self.__data)

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self.__data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "%s(path='%s', files=set(%s))"
        return blurb % (type(self).__name__, self.path, sorted(self.__data))

    def __str__(self):
        """String reprentation of the singleton files."""
        return "\n".join(list(self.output()))

    @property
    def path(self):
        """Directory in which the contained files are located."""
        return self._path

    @path.setter
    def path(self, val):
        self._path = str(val or "")

    def add(self, item):
        """Defining item addition logic (per standard set)."""
        self.__data.add(str(item))

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        self.__data.discard(item)

    def update(self, iterable):
        """Defining item update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def output(self):
        """Return a formatted list of all contained file sequences."""
        for file_name in sorted(self):
            yield os.path.join(self.path, file_name)
