"""Classes utilized by the Seqparse class."""

# Standard Libraries
import os
from collections import MutableMapping, MutableSet
from functools import total_ordering

from .files import File
from .sequences import FileSequence

__all__ = ("FileExtension", "FileSequenceContainer", "SingletonContainer")

###############################################################################
# Class: FileExtension


class FileExtension(MutableMapping):
    """
    Container for frame sequences, indexed by zero-padding.

    Args:
        name (str, optional): The file extension used by the contents of the
            container (ie, "exr", "tif").
        parent (FileSequenceContainer, optional): The container from which this
            instance was spawned.
    """

    _CHILD_CLASS = FileSequence

    def __init__(self, name=None, parent=None):
        """Initialise the instance."""
        self._data = dict()
        self._name = None
        self._parent = None

        self.name = name
        self.parent = parent

    def __delitem__(self, key):
        """Define key deletion logic (per standard dictionary)."""
        del self._data[key]

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self._data:
            opts = dict(ext=self.name, pad=key)
            if self.parent:
                opts.update(name=self.parent.full_name)
            self._data[key] = self._CHILD_CLASS(**opts)
        return self._data[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self._data)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self._data)

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = "{cls}(name={name!r}, pads={pads})"
        return blurb.format(
            cls=type(self).__name__, name=self.name, pads=sorted(self))

    def __setitem__(self, key, value):
        """Define item setting logic (per standard dictionary)."""
        if isinstance(value, (list, tuple, set)):
            opts = dict(ext=self.name, frames=value, pad=key)
            if self.parent:
                opts.update(name=self.parent.full_name)
            value = self._CHILD_CLASS(**opts)

        if not isinstance(value, self._CHILD_CLASS):
            blurb = 'Container may only hold "{}" instances ("{}" provided)'
            raise ValueError(
                blurb.format(self._CHILD_CLASS.__name__, type(value).__name__))

        self._data[key] = value

    @property
    def name(self):
        """str: name of the file extension."""
        return self._name

    @name.setter
    def name(self, val):
        self._name = None
        if val:
            self._name = str(val)

    @property
    def parent(self):
        """FileSequenceContainer: parent of the instance."""
        return self._parent

    @parent.setter
    def parent(self, val):
        self._parent = None
        if isinstance(val, FileSequenceContainer):
            self._parent = val

    def output(self):
        """
        Calculate a sorted list of all contained file extentions.

        Yields:
            FrameSequence, sorted by zero-pad length.
        """
        # First, check to see if we need to consolidate our file sequences.
        data = sorted(list(self.items()), reverse=True)
        while len(data) > 1:
            pad, fseq = data.pop(0)

            # NOTE: the is_padded() method will force recalculation if the
            # object is dirty.
            if not fseq.is_padded:
                prev_fseq = data[0][1]
                prev_fseq.update(fseq)
                del self[pad]

        for pad in sorted(self):
            yield self[pad]


###############################################################################
# Class: FileSequenceContainer


@total_ordering
class FileSequenceContainer(MutableMapping):
    """
    Container for file sequences, indexed by file extension.

    Args:
        name (str, optional): Base name of the contained files.
        file_path (str, optional): Directory in which the contained files
            reside.
    """

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
        """
        Define equality between instances.

        NOTE: Equality is solely based upon comparison of the "full_name"
        property and is only used for output sorting.
        """
        if type(other) is type(self):
            return self.full_name == other.full_name
        return False

    def __getitem__(self, key):
        """Define key getter logic (per collections.defaultdict)."""
        if key not in self._data:
            self._data[key] = self._CHILD_CLASS(name=key, parent=self)
        return self._data[key]

    def __iter__(self):
        """Define key iteration logic (per standard dictionary)."""
        return iter(self._data)

    def __len__(self):
        """Define item length logic (per standard dictionary)."""
        return len(self._data)

    def __lt__(self, other):
        """
        Define whether one instance may be sorted below another.

        NOTE: Equality is solely based upon comparison of the "full_name"
        property and is only used for output sorting.
        """
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
        if not isinstance(value, self._CHILD_CLASS):
            blurb = 'Container may only hold "{}" instances ("{}" provided)'
            raise ValueError(
                blurb.format(self._CHILD_CLASS.__name__, type(value).__name__))

        elif key != value.name:
            blurb = ("Key value must match extension name of provided value "
                     "({!r} != {!r})")
            raise ValueError(blurb.format(key, value.name))

        self._data[key] = value
        # Overriding child container's name to match!
        value.name = self.full_name

    @property
    def full_name(self):
        """str: Full (base) name of the file sequence."""
        return self._full

    @property
    def name(self):
        """str: Base name of the file sequence (no containing directory)."""
        return self._name

    @name.setter
    def name(self, val):
        self._name = None
        if val:
            self._name = str(val)
        self._full = os.path.join(self._path or "", self._name or "")

    @property
    def path(self):
        """str: directory in which the contained files reside."""
        return self._path

    @path.setter
    def path(self, val):
        self._path = None
        if val:
            self._path = str(val)
        self._full = os.path.join(self._path or "", self._name or "")

    def output(self):
        """
        Calculate a sorted list of all contained file sequences.

        Yields:
            FileSequence, sorted (in order) by file path, extension, and zero-
                padding length.
        """
        for data in sorted(self.values()):
            for file_seq in data.output():
                yield file_seq


###############################################################################
# class: SingletonContainer


class SingletonContainer(MutableSet):
    """
    Container for singleton files, indexed alphabetically by file path.

    Args:
        file_names (list-like of str, optional): List of base file names to
            store in the container.
        file_path (str, optional): Directory in which the contained files
            reside.
    """

    def __init__(self, file_names=None, file_path=None):
        """Initialise the instance."""
        self._data = set()
        self._path = None
        self._stat = dict()

        for item in file_names or []:
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
        return "\n".join(list(map(str, self.output())))

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
        """
        Cache file system stat data for the specified file base name.

        Input disk stat value will be stored in a new stat_result
        instance.

        Args:
            base_name (str): Base name of the file for which the supplied disk
                stats are being cached.
            input_stat (stat_result): Value that you'd like to cache.

        Returns:
            stat_result that was successfully cached.
        """
        from . import get_stat_result

        self._stat[base_name] = get_stat_result(input_stat)
        return self._stat[base_name]

    def output(self):
        """
        Calculate formatted list of all contained file sequences.

        Yields:
            File, sorted alphabetically.
        """
        for file_name in sorted(self):
            yield File(
                os.path.join(self.path, file_name), self.stat(file_name))

    def stat(self, base_name=None):
        """
        Individual file system status, indexed by base name.

        This method only returns cached disk stats (if any exist). Use the
        `cache_stat` method if you'd like to set new values.

        Args:
            base_name (str, optional): Base name of the file for which you'd
                like to return the disk stats.

        Returns:
            None if a file has been specified but disk stats have not been
            cached.
            stat_result if a file has been specified and disk stats have
            been previously cached.
            dict of disk stats, indexed by str base name if no name has been
            specified.
        """
        if base_name is None:
            return self._stat
        return self._stat.get(base_name, None)
