# Changes

## Unreleased

Changes (from v1.0.1)

Breaking changes:

* Requires Python 3.11 or later (was 3.7+), and no longer depends on `six`.
* `SeqparsePadException` is now `SeqparsePadError`, a subclass of
  `ValueError`. As a result `validate_frame_sequence()` no longer raises on bad
  padding.
* Exceptions are standardized: wrong value types raise `TypeError`, and a
  missing extension raises `ValueError`.
* Scanning no longer hides symlinked directories that are not loops: a file
  reachable by two paths is listed under each, like `find -L`. Only a directory
  that resolves to one of its own ancestors is skipped.

New features:

* `seqls -` reads file names from standard input (one per line) and groups
  them without touching disk, eg `find . -name '*.exr' | seqls -`.
* `seqls --json` prints machine-readable JSON (see the README for the fields).
* `seqcp` and `seqmv` copy, move and renumber file sequences (`--offset`,
  `--start`, `--name`, `--pad`), with a dry run (`-n`) and safety checks:
  nothing is overwritten unless `-f` is given, everything is checked before the
  first file is touched, and a failure part way is undone. `seqparse.transfer`
  is the library API (`plan_move`, `plan_copy`).
* `seqls --empty` lists the zero-byte frames of each sequence (the debris of a
  crashed render); `FileSequence.empty_files()` is the library equivalent.
* Windows is supported: native paths, including drive letters, UNC shares and
  mixed separators, and CI now runs on Windows, macOS and Linux.
* Fully type-annotated (mypy strict) and ships a `py.typed` marker (PEP 561),
  so type checkers use seqparse's annotations.
* `__all__` is complete in every module (added `get_stat_result`, `StatLike`,
  `FrameChunk`, `ScanOptions`, `Location`, the regex result types and the
  `seqls` functions), and a test keeps it that way.

Performance:

* Frames are stored in a compact sorted array: peak memory falls to 3-18% of
  1.0.1's and most operations run 2-14x faster.
* Frame strings and file names are parsed without per-chunk regex matches, and
  possessive regexes stop large inputs from using megabytes of backtracking
  state.
* Directory scans are faster (inode-based symlink-loop detection, uncopied stat
  results).
* Instances use `__slots__`; weak references, custom attributes and pickles
  made by 1.0.x still work.

Bug fixes:

* *Bugfix:* Type annotations: `scan_path()`, `add_file()`, `File` and
  `FileSequence` accept `os.PathLike` (eg `pathlib.Path`) as they always did
  at runtime, so type checkers no longer reject it.
* *Bugfix:* Scanning: depth limits were ignored for lists of paths,
  `--mindepth` was off by one, a trailing slash shifted depths, symlink loops
  caused infinite recursion, and one unreadable subdirectory aborted the whole
  scan. Scanning a single file now classifies it like a directory scan does,
  so a file named like `foo.1-3.exr` is one file with its real stats.
* *Bugfix:* File sequences: crashes and mangled names with frame-only file
  names, base names that look like sequences, cloning, partially stat'd
  sequences, frame 0 and containers with several extensions; stale `str()`
  output after changing a sequence's pad; sequences losing their base name and
  path in some containers; `FileSequence("foo.0001-0003.exr", ext="exr")` now
  parses.
* *Bugfix:* `in` and `.get()` on sequence containers always succeeded and
  silently created empty entries, and so did `pop()` and `setdefault()`.
* *Bugfix:* Scanning no longer aborts on a symlink that loops onto itself or
  points somewhere unreadable; the entry is skipped.
* *Bugfix:* `FileSequence.size`, `mtime` and `ctime` now follow stats cached
  after the sequence was first formatted (they stayed `None` or stale).
* *Bugfix:* `1.5 in FrameSequence(...)` and `in FrameChunk(...)` are now
  `False` (1.5 was truncated to frame 1), and `discard(float("inf"))` is
  ignored instead of raising `OverflowError`.
* *Bugfix:* `seqls` output: blank lines from `--missing`, "----" shown as the
  size of 0-byte files, and the current time shown for entries without stats.
* `File` objects are now hashable.
* Fixed Python 2 `print` syntax in the `invert()` and
  `validate_frame_sequence()` docstring examples.

Project:

* All packaging metadata lives in `pyproject.toml`, and the tests are no longer
  shipped in wheels.
* README and changelog are Markdown; the stale Sphinx docs are replaced by API
  docs built with pdoc and published at https://hoafaloaf.github.io/seqparse/.
* The examples in the docstrings are tested (and the broken ones fixed).
* GitHub Actions replaces Travis (ruff and mypy replace yapf, isort and pylint)
  and uploads coverage to Coveralls.
* The test suite grew from 60 to 168 tests, and coverage is at 99%.

## v1.0.1 (2022/09/13)

Changes (from v0.7.2)

* First update in 5 years -- thanks, Frank Reuter!
* Heavy refactor for modern Python; Added support for Python 3.7 - 3.10,
  dropped support for versions < 3.7.
* Started migration to `pyproject.toml` (mostly there).
* No changes in functionality.

## v0.7.2 (2017/12/08)

Changes (from v0.7.1)

* No changes in functionality.
* Changed `print XXX` to `print(XXX)` in all docstrings.

## v0.7.1 (2017/12/08)

Changes (from v0.7.0)

* Frame sequences similar to `[1, 3, 4, 5]` are now expressed correctly (ie,
  **1,3-5** instead of **1,3,4,5**).

## v0.7.0 (2017/04/18)

Changes (from v0.6.4)

* `Seqparse.scan_path()` can now accept list-like collections of input search
  paths and deals with them recursively.
* Moved all stat-related methods and properties from the `FrameSequence` to
  the `FileSequence` class.
* `FileExtension` now hold `FileSequence` instances (which makes more
  sense if you think about it).
* `FileExtension.output()` now correctly handles pad consolidation.
* `FileSequence` instances can now clone other `FileSequence` instances.
* `FileSequence` instances now have two new properties: `frames` (which
  iterates over the contained **padded** frames) and `pretty_frames`
  (which returns the string representation of the contained frame sequence).
* `FileSequence.update()` can now accept FileSequence instances as input.
* Coverage tests are pretty much at 100%.

## v0.6.4 (2017/04/08)

Changes (from v0.6.3)

* Rebuilt setup files -- (hopefully) ready for initial release on pypi!

## v0.6.3 (2017/04/07)

Changes (from v0.6.2)

* Miscellaneous updates in preparation for pypi release.

## v0.6.2 (2017/04/06)

Changes (from v0.6.1)

* Updated `README.md` for accuracy on roadmap.

## v0.6.1 (2017/04/06)

Changes (from v0.6.0)

* Added support for **python 3.4+**.
* Packaging changes in preparation for pushing module to PyPi.

## v0.6.0 (2017/04/05)

Changes (from v0.5.0)

* DOCUMENTED ALL THE THINGS!
* Some slight parameter refactoring (ie, iterable -> frame/frames where
  necessary), but no changes in functionality.

## v0.5.0 (2017/04/01)

Changes (from v0.4.0)

* Added ability to query/report disk footprint for all scanned files.
* `seqls`: Implemented new --mindepth and --maxdepth to help limit the depth
  you'll scan while searching for file sequences. They should have exactly the
  same functionality as find's similarly named flags.
* `seqls`: Added `-a/--all` and `-l/--long-format` options to maximize your
  file sequence scanning pleasure. The options should mimic the behaviour of
  the similarly named flags for the ls command. Also, paring up the
  `--long-format` option with the new `-H/--human-readable` option will cause
  `seqls` to report file sizes in a much more legible (gnu-style) fashion.
* `Seqparse`: Now returns all singleton files as `File` instances. As with
  `FileSequence` instances, casting a `File` instance to a string will result
  in the name of the file.
* `FileSequence`, `File`: Added `size` and `mtime` properties that report disk
  footprint and latest file modification time, respectively, for the referenced
  files.
* Renamed all flags with underscores to use dashes instead (hitting the shift
  key can be a drag).

## v0.4.0 (2017/03/22)

Changes (from v0.3.0)

* Added a couple new options to the `seqls` command line tool:
  * `-S/--seqsonly`: Allows the user to filter output to only contain
    discovered file sequences.
  * `-m/--missing`: Allows the user to display the missing files in a
    sequence in the typical file sequence-style output.
* Made output types consistent for all classes -- every `output()` method
  returns class instances, all of which can be safely turned into a displayable
  string via the `str()` method.
* Added `FrameChunk`, `FrameSequence`, and `FileSequence` equality/inequality
  methods.
* Consolidated a lot of the sequence parsing activities in the `Seqparse`
  class.
* Added the `FileSequence` class to represent individual padded file sequences.
  Containment behaviour handles both frame numbers and file names.
* Added the `regex` submodule, home to the new `SeqparseRegexMixin` class. This
  class adds a number of file name/sequence parsing methods that I'm using to
  great effect in a number of classes.
* `FrameSequence` instances can now be instantiated with string frame
  sequences, and their containment behaviour will handle both padded and
  non-padded string frame values as well as integers.
* `FrameSequence.add` will now handle string frame sequences as input as well.
* Refactored all sequence-related classes (`FrameChunk`, `FrameSequence`,
  `FileSequence`) to their own module.
* Removed the `seqparse.get_chunk()` method as `FrameChunks` are really just
  for internal use only.
* Private class attributes were turning out to be a drag, so now they're all
  just protected.
* Overall module coverage is now hovering at around **98%**. Yay.

## v0.3.0 (2017/03/17)

Changes (from v0.2.0)

* *Bugfix:* `FrameSequence.discard()` now handles poorly padded frames
  correctly.
* *Bugfix:* Messages thrown when an incorrect frame padding has been specified
  should now be more correct.
* `FrameChunk` and `FrameSequence` instances may now be reversed via the
  `reversed()` command.
* `FrameChunk` and `FrameSequence` may now be inverted (ie, report back the
  missing frames as a `FrameSequence` instance) via their new `invert` method.
* `.coveragerc` has been updated to exclude `seqparse.test*`.
* Coverage tests for `FrameChunk`, `FrameSequence`, and `Seqparse` are now at
  **100%**!

## v0.2.0 (2017/03/17)

Changes (from v0.1.3)

* `FrameChunk` and `FrameSequence` instances now have similar behaviour when
  used as iterators.
* Testing on Linux-based machines now accepts executable test files (as I'm
  spending half my time programming on a Windows box).
* Yes, we do need some stinkin' badges. `README.md` now indicates build status
  (travis-ci), coverage percentage (coveralls.io), and code health
  (landscape.io).

## v0.1.3 (2017/03/16)

Changes (from v0.1.1)

* Added coveralls support! Now you can look at code coverage for the project on
  coverage.io. And I get to add a pretty badge to the `README.md`.

## v0.1.2 (2017/03/16)

Changes (from v0.1.1)

* Frame sequences may now be directly added to any `Seqparse` instance via the
  add_file method.
* `FrameChunk` instances are now iterable and have proper containment tests for
  both (padded) string and integer frames.
* `FileSequence` and `Singletons` classes have been refactored to
  `FileSequenceContainer` and `SingletonContainer`, respectively, to more
  accurately reflect their functionality.

## v0.1.1 (2017/03/15)

Test/Bugfix Release

Changes (from v.0.1)

* `seqls`: It's accessed the same old way (ie, `seqls` from the command line),
  but it's no longer a dedicated script; it's been moved to
  `seqparse.cli.seqls` to ease installation.
* The test suite has been expanded to cover pretty much everything as it
  currently stands.
* Fixed a bug where the padding on single frames wasn't resolving properly.
* `README.md` updated with a laundry list of stuff I'd like to do before I'm
  moderately satisfied with my coding endeavours.

## v0.1 (2017/03/14)

Initial release with basic functionality.

* Primary usage is via the included `seqls` script.
* May be installed via setuptools-supplied `setup.py`.
* No real documentation (yet).
