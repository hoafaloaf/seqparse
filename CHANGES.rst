CHANGES
=======
v1.0.1 (2022/09/13)
-------------------

Changes (from v0.7.2)

* First update in 5 years -- thanks, Frank Reuter!
* Heavy refactor for modern Python; Added support for Python 3.7 - 3.10,
  dropped support for versions < 3.7.
* Started migration to `pyproject.toml` (mostly there).
* No changes in functionality.

v0.7.2 (2017/12/08)
-------------------

Changes (from v0.7.1)

* No changes in functionality.
* Changed ``print XXX`` to ``print(XXX)`` in all docstrings.

v0.7.1 (2017/12/08)
-------------------

Changes (from v0.7.0)

* Frame sequences similar to ``[1, 3, 4, 5]`` are now expressed correctly (ie,
  **1,3-5** instead of **1,3,4,5**).


v0.7.0 (2017/04/18)
-------------------

Changes (from v0.6.4)

* ``Seqparse.scan_path()`` can now accept list-like collections of input search
  paths and deals with them recursively.
* Moved all stat-related methods and properties from the ``FrameSequence`` to
  the ``FileSequence`` class.
* ``FileExtension`` now hold ``FileSequence`` instances (which makes more
  sense if you think about it).
* ``FileExtension.output()`` now correctly handles pad consolidation.
* ``FileSequence`` instances can now clone other ``FileSequence`` instances.
* ``FileSequence`` instances now have two new properties: ``frames`` (which
  iterates over the contained **padded** frames) and ``pretty_frames``
  (which returns the string representation of the contained frame sequence).
* ``FileSequence.update()`` can now accept FileSequence instances as input.
* Coverage tests are pretty much at 100%.


v0.6.4 (2017/04/08)
-------------------

Changes (from v0.6.3)

* Rebuilt setup files -- (hopefully) ready for initial release on pypi!


v0.6.3 (2017/04/07)
-------------------

Changes (from v0.6.2)

* Miscellaneous updates in preparation for pypi release.


v0.6.2 (2017/04/06)
-------------------

Changes (from v0.6.1)

* Updated ``README.md`` for accuracy on roadmap.


v0.6.1 (2017/04/06)
-------------------

Changes (from v0.6.0)

* Added support for **python 3.4+**.
* Packaging changes in preparation for pushing module to PyPi.


v0.6.0 (2017/04/05)
-------------------

Changes (from v0.5.0)

* DOCUMENTED ALL THE THINGS!
* Some slight parameter refactoring (ie, iterable -> frame/frames where
  necessary), but no changes in functionality.


v0.5.0 (2017/04/01)
-------------------

Changes (from v0.4.0)

* Added ability to query/report disk footprint for all scanned files.
* ``seqls``: Implemented new --mindepth and --maxdepth to help limit the depth
  you'll scan while searching for file sequences. They should have exactly the
  same functionality as find's similarly named flags.
* ``seqls``: Added ````-a/--all`` and ``-l/--long-format`` options to maximize your
  file sequence scanning pleasure. The options should mimic the behaviour of
  the similarly named flags for the ls command. Also, paring up the
  ``--long-format`` option with the new ``-H/--human-readable`` option will cause
  ``seqls`` to report file sizes in a much more legible (gnu-style) fashion.
* ``Seqparse``: Now returns all singleton files as ``File`` instances. As with
  ``FileSequence`` instances, casting a ``File`` instance to a string will result
  in the name of the file.
* ``FileSequence``, ``File``: Added ``size`` and ``mtime`` properties that report disk
  footprint and latest file modification time, respectively, for the referenced
  files.
* Renamed all flags with underscores to use dashes instead (hitting the shift
  key can be a drag).


v0.4.0 (2017/03/22)
-------------------

Changes (from v0.3.0)

* Added a couple new options to the ``seqls`` command line tool:
    * ``-S/--seqsonly``: Allows the user to filter output to only contain
      discovered file sequences.
    * ``-m/--missing``: Allows the user to display the missing files in a
      sequence in the typical file sequence-style output.
* Made output types consistent for all classes -- every ``output()`` method
  returns class instances, all of which can be safely turned into a displayable
  string via the ``str()`` method.
* Added ``FrameChunk``, ``FrameSequence``, and ``FileSequence`` equality/inequality
  methods.
* Consolidated a lot of the sequence parsing activities in the ``Seqparse``
  class.
* Added the ``FileSequence`` class to represent individual padded file sequences.
  Containment behaviour handles both frame numbers and file names.
* Added the ``regex`` submodule, home to the new ``SeqparseRegexMixin`` class. This
  class adds a number of file name/sequence parsing methods that I'm using to
  great effect in a number of classes.
* ``FrameSequence`` instances can now be instantiated with string frame
  sequences, and their containment behaviour will handle both padded and
  non-padded string frame values as well as integers.
* ``FrameSequence.add`` will now handle string frame sequences as input as well.
* Refactored all sequence-related classes (``FrameChunk``, ``FrameSequence``,
  ``FileSequence``) to their own module.
* Removed the ``seqparse.get_chunk()`` method as ``FrameChunks`` are really just
  for internal use only.
* Private class attributes were turning out to be a drag, so now they're all
  just protected.
* Overall module coverage is now hovering at around **98%**. Yay.


v0.3.0 (2017/03/17)
-------------------

Changes (from v0.2.0)

* *Bugfix:* ``FrameSequence.discard()`` now handles poorly padded frames
  correctly.
* *Bugfix:* Messages thrown when an incorrect frame padding has been specified
  should now be more correct.
* ``FrameChunk`` and ``FrameSequence`` instances may now be reversed via the
  ``reversed()`` command.
* ``FrameChunk`` and ``FrameSequence`` may now be inverted (ie, report back the
  missing frames as a ``FrameSequence`` instance) via their new ``invert`` method.
* ``.coveragerc`` has been updated to exclude ``seqparse.test*``.
* Coverage tests for ``FrameChunk``, ``FrameSequence``, and ``Seqparse`` are now at
  **100%**!

v0.2.0 (2017/03/17)
-------------------

Changes (from v0.1.3)

* ``FrameChunk`` and ``FrameSequence`` instances now have similar behaviour when
  used as iterators.
* Testing on Linux-based machines now accepts executable test files (as I'm
  spending half my time programming on a Windows box).
* Yes, we do need some stinkin' badges. ``README.md`` now indicates build status
  (travis-ci), coverage percentage (coveralls.io), and code health
  (landscape.io).

v0.1.3 (2017/03/16)
-------------------

Changes (from v0.1.1)

* Added coveralls support! Now you can look at code coverage for the project on
  coverage.io. And I get to add a pretty badge to the ``README.md``.

v0.1.2 (2017/03/16)
-------------------

Changes (from v0.1.1)

* Frame sequences may now be directly added to any ``Seqparse`` instance via the
  add_file method.
* ``FrameChunk`` instances are now iterable and have proper containment tests for
  both (padded) string and integer frames.
* ``FileSequence`` and ``Singletons`` classes have been refactored to
  ``FileSequenceContainer`` and ``SingletonContainer``, respectively, to more
  accurately reflect their functionality.


v0.1.1 (2017/03/15)
-------------------

Test/Bugfix Release

Changes (from v.0.1)

* ``seqls``: It's accessed the same old way (ie, ``seqls`` from the command line),
  but it's no longer a dedicated script; it's been moved to
  ``seqparse.cli.seqls`` to ease installation.
* The test suite has been expanded to cover pretty much everything as it
  currently stands.
* Fixed a bug where the padding on single frames wasn't resolving properly.
* ``README.md`` updated with a laundry list of stuff I'd like to do before I'm
  moderately satisfied with my coding endeavours.

v0.1 (2017/03/14)
-----------------

Initial release with basic functionality.

* Primary usage is via the included ``seqls`` script.
* May be installed via setuptools-supplied ``setup.py``.
* No real documentation (yet).
