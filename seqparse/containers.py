"""Classes utilized by the Seqparse class."""

# Standard Libraries
import copy
import os
from collections import MutableMapping, MutableSet
from functools import total_ordering

from posix import stat_result

from .files import File
from .sequences import FileSequence, FrameSequence

__all__ = ("FileExtension", "FileSequenceContainer", "SingletonContainer")

###############################################################################
# Class: FileExtension


class FileExtension(MutableMapping):
    """Container for frame sequences, indexed by zero-padding."""

    _CHILD_CLASS = FrameSequence

    def __init__(self, name=None):
        """Initialise the instance."""
        self._data = dict()
        self._name = None

        self.name = name

    def __delitem__(self, key):
        """Define key deletion logic (per standard dictionary)."""
        del self._data[key]

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self._data:
            self._data[key] = self._CHILD_CLASS(pad=key)
        return self._data[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self._data)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self._data)

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

        self._data[key] = value

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
                # Copying in the current pad's file stats (if any).
                prev_frames.stat.update(copy.deepcopy(self[pad].stat))

                del self[pad]

        for pad in sorted(self):
            yield self[pad]


###############################################################################
# Class: FileSequenceContainer


@total_ordering
class FileSequenceContainer(MutableMapping):
    """Representative for file sequences, indexed by file extension."""

    _CHILD_CLASS = FileExtension

    def __init__(self, name=None, file_path=None):
        """Initialise the instance."""
        self._data = dict()

        self._full = None
        self._name = None
        self._path = None

        self.name = name
        self.path = file_path

    def __delitem__(self, key):
        """Define key deletion logic (per standard dictionary)."""
        del self._data[key]

    def __eq__(self, other):
        """Define equality between instances."""
        if type(other) is type(self):
            return self.full_name == other.full_name
        return False

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self._data:
            self._data[key] = self._CHILD_CLASS(name=key)

        return self._data[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self._data)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self._data)

    def __lt__(self, other):
        """Define equality between instances."""
        if type(other) is type(self):
            return self.full_name < other.full_name
        return True

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "{cls}(full_name={full_name!r}, exts={exts})"
        return blurb.format(
            cls=type(self).__name__,
            exts=sorted(self),
            full_name=self.full_name)

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._CHILD_CLASS(value)

        if not isinstance(value, self._CHILD_CLASS) or value is None:
            raise ValueError

        self._data[key] = value

    @property
    def full_name(self):
        """The full (base) name of the file sequence."""
        return self._full

    @property
    def name(self):
        """The (base) name of the file sequence."""
        return self._name

    @name.setter
    def name(self, val):
        self._name = None
        if val:
            self._name = str(val)
        self._full = os.path.join(self._path or "", self._name or "")

    @property
    def path(self):
        """Directory in which the contained files are located."""
        return self._path

    @path.setter
    def path(self, val):
        self._path = None
        if val:
            self._path = str(val)
        self._full = os.path.join(self._path or "", self._name or "")

    def output(self):
        """Return a sorted list of all contained file sequences."""
        for ext, data in sorted(self.items()):
            for frame_seq in data.output():
                file_seq = FileSequence(
                    self.full_name, frames=frame_seq, ext=ext)
                yield file_seq


###############################################################################
# class: SingletonContainer


class SingletonContainer(MutableSet):
    """Representative for singleton files."""

    def __init__(self, iterable=None, file_path=None):
        """Initialise the instance."""
        self._data = set()
        self._path = None
        self._stat = dict()

        for item in iterable or []:
            self.add(item)

        self.path = file_path

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        return str(item) in self._data

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        return iter(self._data)

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self._data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "%s(path='%s', files=set(%s))"
        return blurb % (type(self).__name__, self.path, sorted(self._data))

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
        self._data.add(str(item))

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        self._data.discard(item)

    def update(self, iterable):
        """Defining item update logic (per standard set)."""
        for item in iterable:
            self.add(item)

    def cache_stat(self, base_name, input_stat):
        """Cache file system stat data for the specified file base name."""
        self._stat[base_name] = stat_result(input_stat)
        return self._stat[base_name]

    def output(self):
        """Return a formatted list of all contained file sequences."""
        for file_name in sorted(self):
            yield File(
                os.path.join(self.path, file_name), self.stat(file_name))

    def stat(self, base_name=None):
        """Individual file system status, indexed by base name."""
        if base_name is None:
            return self._stat
        return self._stat.get(base_name, None)
