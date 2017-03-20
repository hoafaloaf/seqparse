"""Container for all regular expressions used by the seqparse module."""

__all__ = ("BITS_EXPR", "FILE_NAME_EXPR", "FRAME_EXPR", "FRAME_SEQ_EXPR")

# BITS_EXPR is used to split a frame "chunk" into three sections: first
# (frame), last (frame). and step.
BITS_EXPR = r"(?P<first>\d+)(?:-(?P<last>\d+)(?:x(?P<step>\d+)?)?)?$"

# FILE_NAME_EXPR is used to split a file name into three sections: base (name),
# frame (chunk), and file ext(ension).
FILE_NAME_EXPR = r"(?P<base>.*)\.(?P<frame>\d+)\.(?P<ext>[^\.]+)$"

# FRAME_EXPR is used to validate a "legal" sequence of frames.
FRAME_EXPR = r"(?:\d+(?:-\d+(?:x\d+)?)?(?:,+\d+(?:-\d+(?:x\d+)?)?)*)"

# FRAME_SEQ_EXPR is used to validate and split a "legal" sequence of files into
# three sections: base (name), frame (sequence), and file ext(ension).
FRAME_SEQ_EXPR = r"(?P<base>.*)\.(?P<frame>%s)\.(?P<ext>[^\.]+)$" % FRAME_EXPR
