"""Classes utilized by the Seqparse class."""

# Standard Libraries
import os
from collections import MutableMapping, MutableSet

from .sequences import FrameSequence

__all__ = ("FileExtension", "FileSequenceContainer", "SingletonContainer")

###############################################################################
# Class: FileExtension


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
        """The name of the file extension."""
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
                prev_frames = data[0][1]
                prev_frames.update(frames)
                del self[pad]

        for pad, frames in sorted(self.items()):
            yield str(frames)


###############################################################################
# Class: FileSequenceContainer


class FileSequenceContainer(MutableMapping):
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
# class: SingletonContainer


class SingletonContainer(MutableSet):
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
