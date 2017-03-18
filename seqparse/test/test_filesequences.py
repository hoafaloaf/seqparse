"""Test the FrameSequence class."""

# Standard Libraries
import unittest

from seqparse.sequences import (FileSequence, FrameChunk, FrameSequence,
                                SeqparsePadException)


###############################################################################
# class: TestFrameSequences


class TestFileSequences(unittest.TestCase):
    """Test basic functionality on the FileSequence class."""

    _test_name = "cat"
    _test_path = "/pretty/kitty"

    def setUp(self):
        """Set up the test instance."""

    def test_properties(self):
        """Test getting/setting simple properties."""
        fseq = FileSequence()
        print "name:", fseq.name
        print "path:", fseq.path
