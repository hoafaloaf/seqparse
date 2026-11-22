# Plan: making seqparse more useful

Work through the items in order, one at a time (or a small batch of the quick
wins). Plan each item against the current code before starting it: earlier
items change what later ones touch. Tick an item off (`[x]`) in the commit
that completes it; if CI then fails, fix forward.

Every item is done when: tests cover the change, `ci-run_tests` passes, the
README and `CHANGES.md` mention user-visible changes, and CI is green on all
three OSes. See `CLAUDE.md` for commands and conventions.

## Quick wins

- [x] **1. Ship a `py.typed` marker.** Without it, users' type checkers ignore
  seqparse's annotations. setuptools (>=77, our floor) includes `py.typed`
  automatically; a CI `package` job asserts it is in the wheel and the sdist.
- [x] **2. Accurate `__all__`.** Every module already had `__all__`, but the
  lists were stale. They now name everything a user can pass to or receive
  from the API, and `test_public_api.py` fails when they drift. Raw `dir()`
  still lists imported names: hiding them (module `__dir__`, or underscore
  import aliases) was rejected, because `py.typed` already makes type checkers
  hide them and the aliases would break the Windows-simulation tests.
- [x] **3. `seqls --json`.** Machine-readable output: one object per item with
  name, path, ext, frames (string form), pad, missing frames, and with `-l`
  the size and mtime. Document the schema in the README.
- [x] **4. Flag suspicious frames in `seqls`.** `--empty` lists the 0-byte
  frames (common after crashed renders), via `FileSequence.empty_files()` and
  the existing stat caching; no extra stat calls when the flag is off. Size
  outliers were considered and dropped: file sizes vary naturally (EXR
  compression), so any threshold gives false alarms.
- [x] **5. Read names from stdin.** `find … | seqls -` groups names without
  scanning disk, via `Seqparse.add_file`. `-l` and `--empty` are rejected with
  it (the names need not exist).

## Moderate effort

- [ ] **6. Sequence pattern formats.** Render a `FileSequence` in the
  notations other tools use, and parse them back with a frame range:
  `plate.%04d.exr` (printf: ffmpeg, Nuke), `plate.####.exr` (Nuke, RV),
  `plate.$F4.exr` (Houdini), `plate.@@@@.exr`. Settle the API first (for
  example `fseq.format("printf")` and a constructor taking a pattern plus
  frames) and keep the existing string forms unchanged.
- [ ] **7. Negative frames.** Accept frames below 0 (`-0010-0005`, handles and
  pre-roll). Touches the regexes, `FrameChunk` and padding rules; decide how
  padding counts the sign. Benchmark before and after.
- [ ] **8. API docs on GitHub Pages.** Generate a reference from the
  docstrings (for example MkDocs with mkdocstrings), built and deployed by a
  CI workflow. Pages is already enabled (currently serving the repo root of
  `master`); switch its source to the workflow.

## Discuss with the user before starting

- [ ] **9. Renumber, copy and move sequences.** For example "shift 1–100 to
  1001–1100", with a dry run, collision checks and Windows support. Touches
  the filesystem, so agree on the API and safety rules first.
- [ ] **10. Subframes** (`1001.25`) for motion-blur and simulation caches.
  Niche, and conflicts with the integer array storage that makes seqparse
  fast.

## Outside this plan (for the user)

- Renew the Coveralls GitHub connection and revoke the old leaked repo token.
- Decide when to bump the version and release (never without being asked).
  When a release is on PyPI, change the README's install section back to
  `pip install seqparse` and drop the note about the old PyPI version.
