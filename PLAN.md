# Plan: making seqparse more useful

Work through the items in order, one at a time (or a small batch of the quick
wins). Plan each item against the current code before starting it: earlier
items change what later ones touch. Tick an item off (`[x]`, with the commit
hash) once it is committed with CI green.

Every item is done when: tests cover the change, `ci-run_tests` passes, the
README and `CHANGES.md` mention user-visible changes, and CI is green on all
three OSes. See `CLAUDE.md` for commands and conventions.

## Quick wins

- [ ] **1. Ship a `py.typed` marker.** Without it, users' type checkers ignore
  seqparse's annotations. Add `seqparse/py.typed`, include it as package data,
  and confirm it is in the built wheel.
- [ ] **2. Clean public namespace.** `dir(seqparse)` exposes `Any`,
  `Iterable`, `Sequence`, `os`, `TYPE_CHECKING` and `annotations`. Define
  `__all__` in each public module (and keep imports module-style). Do not
  remove anything users could already rely on (`get_parser`, `get_sequence`,
  `invert`, `validate_frame_sequence`, `get_version`, `get_stat_result`,
  submodules).
- [ ] **3. `seqls --json`.** Machine-readable output: one object per item with
  name, path, ext, frames (string form), pad, missing frames, and with `-l`
  the size and mtime. Document the schema in the README.
- [ ] **4. Flag suspicious frames in `seqls`.** For example `--empty` to list
  0-byte frames (common after crashed renders), possibly also size outliers.
  Reuse the existing stat caching; avoid extra stat calls when the flag is
  off.
- [ ] **5. Read names from stdin.** `find … | seqls -` (or `--stdin`) groups
  names without scanning disk, via `Seqparse.add_file`.

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
