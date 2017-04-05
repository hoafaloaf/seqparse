"""Container for all regular expressions used by the seqparse module."""

# Standard Libraries
import re

__all__ = ("BITS_EXPR", "FILE_NAME_EXPR", "FRAME_EXPR", "FILE_SEQ_EXPR",
           "SeqparseRegexMixin")

# BITS_EXPR is used to split a frame "chunk" into three sections: first
# (frame), last (frame). and step.
BITS_EXPR = r"(?P<first>\d+)(?:-(?P<last>\d+)(?:x(?P<step>\d+)?)?)?$"

# FILE_NAME_EXPR is used to split a file name into three sections: base (name),
# frame (chunk), and file ext(ension).
FILE_NAME_EXPR = r"(?:^(?P<name>.+)\.|^)(?P<frame>\d+)\.(?P<ext>[^\.]+)$"

# FRAME_EXPR is used to validate a "legal" sequence of frames.
FRAME_EXPR = r"(?:\d+(?:-\d+(?:x\d+)?)?(?:,+\d+(?:-\d+(?:x\d+)?)?)*)"

# FILE_SEQ_EXPR is used to validate and split a "legal" sequence of files into
# three sections: base (name), frame (sequence), and file ext(ension).
FILE_SEQ_EXPR = r"(?:^(?P<name>.+)\.|^)(?P<frames>%s)\.(?P<ext>[^\.]+)$"
FILE_SEQ_EXPR = FILE_SEQ_EXPR % FRAME_EXPR


###############################################################################
# Class: SeqparseRegexMixin
class SeqparseRegexMixin(object):
    """Base for classes that need to perform regular expression matches."""

    _bits_expr = re.compile(BITS_EXPR)
    _file_expr = re.compile(FILE_NAME_EXPR)
    _frame_expr = re.compile(r",*%s,*$" % FRAME_EXPR)
    _fseq_expr = re.compile(FILE_SEQ_EXPR)

    def __init__(self):
        """Initialise the instance."""
        pass

    def bits_match(self, val, as_dict=False):
        """
        Calculate first, last, step for valid string frame chunks.

        Args:
            val (str): Input chunk of a frame range.
            as_dict (bool, optional): Whether to output return values as a
                dict of regex groups. Defaults to False.

        Returns:
            None if input is an invalid chunk,
            tuple consisting of (first frame, last frame, frame step) with
            as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        bmatch = self._bits_expr.match(val)
        return self._return_value(bmatch, as_dict)

    def file_name_match(self, val, as_dict=False):
        """
        Calculate base name, frame, extension for valid string file name.

        Args:
            val (str): Input file name.
            as_dict (bool, optional): Whether to output return values as a
                dict of regex groups. Defaults to False.

        Returns:
            None if input is an invalid sequence file name,
            tuple consisting of (base name, frame, extension) with
            as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        fmatch = self._file_expr.match(val)
        return self._return_value(fmatch, as_dict)

    def file_seq_match(self, val, as_dict=False):
        """
        Calculate base name, sequence, extension for valid file sequence.

        Args:
            val (str): Input file sequence.
            as_dict (bool, optional): Whether to output return values as a
                dict of regex groups. Defaults to False.

        Returns:
            None if input is an invalid sequence file sequence,
            tuple consisting of (base name, frame sequence, extension) with
            as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        fmatch = self._fseq_expr.match(val)
        return self._return_value(fmatch, as_dict)

    def is_frame_sequence(self, val):
        """
        Whether a string frame sequence is valid.

        Args:
            val (str): Input frame sequence.

        Returns:
            True if frame sequence is valid, False if it is not.
        """
        return bool(self._frame_expr.match(val))

    @staticmethod
    def _return_value(regex_match, as_dict):
        """
        Return match data as tuple or dictionary.

        Args:
            regex_match (SRE_Match): Regex match or None, depending on Whether
                the calling method was a valid match.
            as_dict (bool): Whether to return as a dict of regex groups.

        Returns:
            None if input is an invalid match,
            tuple as_dict = False, or
            dict of regex groups with as_dict = True.
        """
        if not regex_match:
            return None
        if as_dict:
            return regex_match.groupdict()
        return regex_match.groups()
