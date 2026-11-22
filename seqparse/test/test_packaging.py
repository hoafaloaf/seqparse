"""Packaging facts that users depend on."""

from importlib import resources
import unittest


class TestTypedMarker(unittest.TestCase):
    """The PEP 561 marker."""

    def test_py_typed_marker_exists(self):
        """Without py.typed, users' type checkers ignore our annotations."""
        marker = resources.files("seqparse").joinpath("py.typed")
        self.assertTrue(marker.is_file())
