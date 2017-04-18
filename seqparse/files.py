"""Singleton file-related data structures utilized by the Seqparse module."""

# Standard Libraries
import os
from functools import total_ordering

__all__ = ("File", )

###############################################################################
# Class: File


@total_ordering
class File(object):
    """
    Simple representation of files on disk.

    Args:
        file_name (str): Full path to the input file.
        stat (stat_result, optional): Disk stats you'd like to cache for the
            specified file.
    """

    def __init__(self, file_name, stat=None):
        """Initialise the instance."""
        self._info = dict(full=None, name=None, path=None)
        self._stat = None

        self._cache_stat(stat)
        self._set_name(file_name)

    def __eq__(self, other):
        """Define equality between instances."""
        if type(other) is type(self):
            return self.full_name == other.full_name
        return False

    def __lt__(self, other):
        """Define equality between instances."""
        if type(other) is type(self):
            return self.full_name < other.full_name
        return True

    def __repr__(self):  # pragma: no cover
        """Pretty representation of the instance."""
        blurb = ("{cls}({full!r})")
        return blurb.format(cls=type(self).__name__, **self._info)

    def __str__(self):
        """String representation of a File instance."""
        return str(self.full_name)

    @property
    def full_name(self):
        """str: Full name of the sequence, including containing directory."""
        return self._info["full"]

    @property
    def mtime(self):
        """
        int: Modification time of the file.

        Returns None if the files have not been stat'd on disk.
        """
        if not self._stat:
            return None
        return self._stat.st_mtime

    @property
    def name(self):
        """str: Base name of the file sequence (no containing directory)."""
        return self._info["name"]

    @property
    def path(self):
        """str: Directory in which the contained files are located."""
        return self._info["path"]

    @property
    def size(self):
        """
        int: Size of the file in bytes.

        Returns None if the files have not been stat'd on disk.
        """
        if not self._stat:
            return None
        return self._stat.st_size

    def _cache_stat(self, input_stat):
        """
        Cache file system stat data.

        Args:
            input_stat (stat_result): Value that you'd like to cache.

        Returns:
            stat_result that was successfully cached.
        """
        from . import get_stat_result

        self._stat = None
        if input_stat:
            self._stat = get_stat_result(input_stat)
        return self._stat

    def _set_name(self, full_name):
        """
        Set all name-related fields on the instance.

        Args:
            full_name (str): Full path to the contained file.

        Returns:
            dict of path-related strings (full name, base name, path).
        """
        path_name, file_name = os.path.split(full_name)
        self._info.update(full=full_name, name=file_name, path=path_name)
        return self._info

    def stat(self, force=False, lazy=False):
        """
        File system status.

        Args:
            force (bool, optional): Whether to force disk stat query,
                regardless of caching status.
            lazy (bool, optional): Whether to query disk stats should no cached
                value exist.

        Returns:
            None if a frame has been specified but disk stats have not been
            cached.
            stat_result if a frame has been specified and disk stats have
            been previously cached.
        """
        if force or (lazy and self._stat is None):
            self._cache_stat(os.stat(self.full_name))
        return self._stat
