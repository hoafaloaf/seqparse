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

Install the current version from GitHub:

```console
pip install git+https://github.com/hoafaloaf/seqparse
```

(The release on PyPI, 0.7.3 from 2017, is much older and predates support for
current Python versions, so a plain `pip install seqparse` is not recommended
yet.)

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
             [--mindepth MIN_LEVELS] [-m | --empty] [-S] [--json] [-v]
             [search_path ...]

Command line tool for listing file sequences. Upon installation of the package
this script will be accessible via `seqls` command on the command line of your
choice.

positional arguments:
  search_path           Paths that you'd like to search for file sequences.
                        Use '-' to read file names (one per line) from
                        standard input instead; they are used as written, so
                        -a, --maxdepth and --mindepth do not apply to them.

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
  --empty               Only report the zero-byte frames of each sequence (the
                        likely debris of a crashed render), as a frame
                        sequence.
  -S, --seqs-only       Whether to filter out all non-sequence files.
  --json                Print JSON instead of text: sizes (bytes) and
                        modification times (epoch seconds) are included with
                        -l/--long, and with -m/--missing only sequences that
                        have gaps are listed.
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

Crashed renders also tend to leave zero-byte frames behind. `--empty` lists
just those, in the same notation (`-l` adds their sizes and dates; it can't be
combined with `-m`):

```console
$ seqls --empty
superhero_cape_v0001.0501-0510.exr
```

### JSON output

For scripts and pipelines, `--json` prints one JSON array instead of text,
and nothing else (no blank line before it):

```console
$ seqls --json -l -S
[
  {
    "type": "sequence",
    "path": "/renders/superhero_cape_v0001",
    "name": "superhero_cape_v0001",
    "ext": "exr",
    "pad": 4,
    "frames": "0001,0002,0004",
    "count": 3,
    "first": 1,
    "last": 4,
    "missing": "0003",
    "empty": "",
    "size": 3000,
    "mtime": 1763798400.0,
    "string": "/renders/superhero_cape_v0001/superhero_cape_v0001.0001,0002,0004.exr"
  }
]
```

Each entry is either a sequence or a singleton file:

| Field | Meaning |
| --- | --- |
| `type` | `"sequence"` or `"file"` |
| `path`, `name` | The directory (`null` for a name without one), and the sequence's base name or the file's name |
| `string` | What the text output prints for the item |
| `ext`, `pad` | Sequences only: extension and zero-padding |
| `frames` | Sequences only: the frame sequence, e.g. `"0001-0500,0600-0800"` |
| `count`, `first`, `last` | Sequences only: number of frames, first and last frame |
| `missing` | Sequences only: the missing frames in the same notation (`""` if none) |
| `empty` | Sequences only: the zero-byte frames in the same notation (`""` if none); `null` unless `-l` or `--empty` is given |
| `size`, `mtime` | Size in bytes and modification time in seconds since the epoch; `null` unless `-l` is given |

The other options work as usual (`-S`, `--maxdepth`, ...). With `-m/--missing`,
only sequences that have gaps are listed, still described by their real
`frames`, and likewise `--empty` for sequences with zero-byte frames; `-H` has no
effect.

### Reading names from stdin

`seqls -` groups file names read from standard input (one per line) instead
of scanning disk, so it also works on listings of files that aren't on a local
disk:

```console
$ find /renders/superhero_cape_v0001 -name '*.exr' | seqls -
/renders/superhero_cape_v0001/superhero_cape_v0001.0001-1000.exr
```

Names are used as written and grouped by directory exactly as spelled
(`./a/f.1.exr` and `a/f.2.exr` are different directories). `-` can be combined
with real paths. `-m`, `-S` and `--json` work as usual, with `null` sizes;
`-a`, `--maxdepth` and `--mindepth` only apply to scanned paths, and `-l` and
`--empty` need files on disk, so they are rejected together with `-`.

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
