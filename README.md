# seqparse: A nifty way to list your file sequences.

[![PyPI version](https://img.shields.io/pypi/v/seqparse)](https://pypi.org/project/seqparse/)
[![Python versions](https://img.shields.io/pypi/pyversions/seqparse)](https://pypi.org/project/seqparse/)
[![CI](https://github.com/hoafaloaf/seqparse/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/hoafaloaf/seqparse/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/coverallsCoverage/github/hoafaloaf/seqparse?branch=master)](https://coveralls.io/github/hoafaloaf/seqparse?branch=master)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/hoafaloaf/seqparse)](https://github.com/hoafaloaf/seqparse/blob/master/LICENSE.txt)

## Overview

The seqparse module may be used to ...

- Scan specified paths for file sequences and "singletons,"
- Construct frame and file sequence from supplied values, and
- Query disk for overall footprint of tracked files.

The module also comes supplied with a simple tool named `seqls` that
allows the user to scan multiple locations for file sequences and
singletons from the command line.

If you're curious about the **regular expressions** used to determine
what is and isn't a valid file sequence, take a look at the
`seqparse.regex` module.

### Requirements

- Python 3.11 or later, on Linux, macOS or Windows.
- [humanize](https://pypi.org/project/humanize/) (installed
  automatically), used by `seqls --long --human-readable`.

seqparse is fully type-annotated and ships a `py.typed` marker, so type
checkers use its hints.

Install with `pip install seqparse`.

### Frame Sequences

Frame sequences are broken down into comma-separated chunks of the
format `first frame`**-**`last frame`**x**`step` where the following
rules apply:

- Frame numbers can be zero-padded,
- Frame step (increment) is always a positive integer,
- The number of digits in a frame may exceed the padding of a sequence,
  eg `001,010,100,1000`,
- Frame chunks with a specified step will **always** consist of three
  or more frames.

Examples of proper frame sequences:

- Non-padded sequence, frames == **(1, 3, 5, 7)**: `1-7x2`
- Four-padded sequence, frames == **(1, 3, 5, 7)**: `0001-0007x2`
- Three-padded sequence, frames == **(11, 13)**: `011,013`
- Two-padded sequence **(1, 3, 5, 7, 11, 13, 102)**:
  `01-07x2,11,13,102`

### File Sequences

Members of a file sequence can be one of two formats:

- `base_name`**.**`frame_sequence`**.**`file_extension`
- `frame_sequence`**.**`file_extension`

Examples of valid file sequences:

- `my_little_pony.1-7x2.exr`
- `/maya/is/very/strange/01-07x2,11,13,102.tif`
- `C:\this\even\works\in\windows\billy.0001-0095.tga`

## seqls

`seqls` is the command line interface for the `seqparse` module.

```text
usage: seqls [-h] [-a] [-H] [-l] [--maxdepth MAX_LEVELS]
             [--mindepth MIN_LEVELS] [-m] [-S] [-v]
             [search_path ...]

Command line tool for listing file sequences. Upon installation of the package
this script will be accessible via `seqls` command on the command line of your
choice.

positional arguments:
  search_path           Paths that you'd like to search for file sequences.

options:
  -h, --help            show this help message and exit
  -a, --all             Do not ignore entries starting with '.'.
  -H, --human-readable  with -l/--long, print sizes in human readable format
                        (e.g., 1K 234M 2G).
  -l, --long            Use a long listing format.
  --maxdepth MAX_LEVELS
                        Descend at most MAX_LEVELS (a non-negative integer)
                        levels of directories below the starting points; 0
                        scans only the starting points themselves.
  --mindepth MIN_LEVELS
                        Do not scan at levels less than MIN_LEVELS (a non-
                        negative integer); 1 scans every level except the
                        starting points.
  -m, --missing         Whether to invert output file sequences to only report
                        the missing frames.
  -S, --seqs-only       Whether to filter out all non-sequence files.
  -v, --version         Print the version and exit.
```

Most of the functionality is self-explanatory, but the `-m/--missing`
option is probably the most useful to users generating large sequences
of frames on multiple servers.

Say you're creating imagery for the latest superhero movie -- and your
render job crashed some time in the early morning.

You're expecting to see something like this ...

```text
superhero_cape_v0001.0001-1000.exr
```

... but not everything rendered.

```console
$ cd /renders/superhero_cape_v0001
$ seqls
superhero_cape_v0001.0001-0500,0600-0800,0990-1000x5.exr
```

You can easily figure out the missing frames, though, with the
`--missing` option:

```console
$ seqls --missing
superhero_cape_v0001.0501-0599,0801,0991-0994,0996-0999.exr
```

## The module

Using the module is fairly simple:

1. Instantiate a parser (`Seqparse` instance).
2. Add files to the parser either
   - via the `add_file` method, or
   - by scanning a list of locations on disk via the `scan_path`
     method.
3. Create an **iterator** for all file sequences (`FileSequence`
   instances) and singletons (`File` instances).
4. ...
5. Profit.

Example (taken from the `Seqparse` docstring), with the following file
structure ...

```text
test_dir/
    TEST_DIR.0001.tif
    TEST_DIR.0002.tif
    TEST_DIR.0003.tif
    TEST_DIR.0004.tif
    TEST_DIR.0010.tif
    SINGLETON.jpg
```

```pycon
>>> from seqparse import seqparse
>>> parser = seqparse.Seqparse()
>>> parser.scan_path("test_dir")
>>> for item in parser.output():
...     print(str(item))
...
test_dir/TEST_DIR.0001-0004,0010.tif
test_dir/SINGLETON.jpg
>>> for item in parser.output(seqs_only=True):
...     print(str(item))
...
test_dir/TEST_DIR.0001-0004,0010.tif
>>> for item in parser.output(missing=True):
...     print(str(item))
...
test_dir/TEST_DIR.0005-0009.tif
```

### Useful Classes

`FrameSequence` instances are pretty useful on their own.

```pycon
>>> import seqparse
>>> seq = seqparse.get_sequence([1, 2, 3, 4, 8], pad=4)
>>> print(repr(seq))
FrameSequence(pad=4, frames=set([1, 2, 3, 4, 8]))
>>> print(seq)
0001-0004,0008
>>> for frame in seq:
...     print(frame)
...
0001
0002
0003
0004
0008
>>> for frame in seq.invert():
...     print(frame)
...
0005
0006
0007
```

As are `FileSequence` instances (which behave similarly; check class
documentation for details).

## Feedback

Lemme know if you have any requests/complaints/suggestions: open an issue at
<https://github.com/hoafaloaf/seqparse/issues>.
