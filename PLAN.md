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
## Agreed: do before the 2.0.0 release (in this order)

- [x] **8. API docs with pdoc, published to GitHub Pages.** Decisions (agreed
  2026-11-22): pdoc (Google-style docstrings, honors `__all__`) rather than
  MkDocs, whose ecosystem is in flux, or Sphinx; the docs are rebuilt and
  deployed from `master` ("latest"). Pages is currently off.
  - Make every docstring example a real doctest (12 of 40 failed) and test
    them (`seqparse/test/test_docstrings.py`).
  - Pin pdoc in a `docs` extra; a CI `docs` job builds the docs on every push;
    `docs.yml` deploys on pushes to master and manual runs; the Pages source
    is "GitHub Actions" (enable it only with the user's OK).
  - Link the site from the README, `[project.urls]` and the repo homepage.
- [ ] **9. Renumber, copy and move sequences.** Decisions (agreed 2026-11-22):
  new module `seqparse/transfer.py` (the data model stays untouched) and two
  commands, `seqcp` and `seqmv`; renumbering is a move in place with
  `--offset` or `--start`.
  - API: `transfer.plan_move()` / `plan_copy()` return a plan (`pairs` in a
    safe order, `problems`); `plan.execute()` does the I/O and returns a
    FileSequence for the result.
  - CLI: `-n` dry run, `-f` overwrite, `--offset`, `--start`, `--name`,
    `--pad`; the source is a sequence in the usual notation (a subset of
    frames is allowed).
  - Safety rules: (1) never overwrite without `--force`; (2) check everything
    before touching a file: sources exist, no two sources share a destination,
    no destination exists, names differing only by case collide on
    case-insensitive filesystems; (3) order overlapping in-place ranges so no
    source is overwritten before it moves (highest frame first for a positive
    offset), and refuse what cannot be ordered; (4) on an error stop, report,
    and undo completed renames best-effort (no atomicity promised); (5) `-n`
    changes nothing; (6) cross-filesystem moves copy, then delete only after a
    successful copy; (7) gaps stay gaps; (8) the pad grows when new frame
    numbers need more digits, unless `--pad` is given; (9) refuse results below
    frame 0 until item 7; (10) copies keep modification times and copy a
    symlink's contents.
  - Tests: real temp directories on all three OSes; a seeded randomized test
    of the overlap ordering (every file's content must end up at the right
    name); injected failures at the Nth file for the undo; a simulated
    cross-filesystem error; Windows case collisions and in-use files;
    mutation checks.
  - Ship `2.0.0rc2` for real-world trials before 2.0.0.

## Discuss with the user before starting

- [ ] **10. Subframes** (`1001.25`) for motion-blur and simulation caches.
  Niche, and conflicts with the integer array storage that makes seqparse
  fast.

## Outside this plan (for the user)

- Renew the Coveralls GitHub connection and revoke the old leaked repo token.
- Decide when to bump the version and release (never without being asked).
  When a release is on PyPI, change the README's install section back to
  `pip install seqparse` and drop the note about the old PyPI version.
