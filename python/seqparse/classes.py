"""Classes utilized by the Seqparse class."""

from collections import MutableMapping, MutableSet

__all__ = ("FileExtension", "FileSequence", "FrameSequence")

###############################################################################
# Class: FrameSequence


class FrameSequence(MutableSet):
    """Representative for zero-padded frame sequences."""

    def __init__(self, pad=1, iterable=None):
        """Initialise the instance."""
        super(FrameSequence, self).__init__()

        self.__set = set()
        self.pad = pad

        for item in iterable or []:
            self.add(item)

    def __iter__(self):
        """Defining item iteration logic (per standard set)."""
        return iter(self.__set)

    def __len__(self):
        """Defining item length logic (per standard set)."""
        return len(self.__set)

    def __contains__(self, item):
        """Defining containment logic (per standard set)."""
        return int(item) in self.__set

    def __repr__(self):
        """String representation of the object instance."""
        blurb = "%s(pad=%d, frames=%s)"
        return blurb % (type(self).__name__, self.pad, self.__set)

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

    def discard(self, item):
        """Defining item discard logic (per standard set)."""
        self.__set.discard(item)

    def update(self, iterable):
        """Defining item update logic (per standard set)."""


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

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            value = self._CHILD_CLASS(value)

        if not isinstance(value, self._CHILD_CLASS) or value is None:
            raise ValueError

        self.__dict__[key] = value
