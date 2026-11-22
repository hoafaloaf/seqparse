# seqparse: notes for Claude

Library for parsing file and frame sequences, plus the `seqls` CLI. Pure
Python, Python 3.11+, one runtime dependency (`humanize`). Work in progress
lives in `PLAN.md`: read it before starting a task and tick items off there.

## Checks (run before every commit)

Use the conda envs `seqparse-py311`, `seqparse-py314` and `seqparse-py315`,
from the repo root. Only `seqparse-py314` has seqparse installed (editable)
along with ruff and mypy; the others have just pytest and humanize.

```sh
PATH=~/miniconda3/envs/seqparse-py314/bin:$PATH bash seqparse/test/ci-run_tests
~/miniconda3/envs/seqparse-py311/bin/python -m pytest -q seqparse   # oldest supported
```

`ci-run_tests` mirrors CI: ruff check, ruff format --check, mypy (strict, must
stay at 0 errors), then pytest under coverage (keep it at 99%+).

For changes to hot paths (`sequences.py`, scanning in `seqparse.py`), compare
against a baseline:

```sh
python benchmarks/bench.py --save /tmp/base.json   # before the change
python benchmarks/bench.py --compare /tmp/base.json
```

CI (`.github/workflows/ci.yml`) runs on Linux, macOS and Windows with Python
3.11–3.15 and uploads coverage to Coveralls. After pushing, watch it with
`gh run watch`.

## Code style

- **Google-style imports:** import modules, never individual symbols
  (`from seqparse import sequences`, then `sequences.FileSequence`;
  `import bisect`, then `bisect.bisect_left`). `typing`, `collections.abc` and
  `typing_extensions` names are the exception. Absolute imports only (ruff
  TID252 enforces it).
- ruff: line length 80, double quotes. mypy strict over `seqparse/`, tests
  excluded.
- **Efficiency comes first** (CPU, then memory). Internals use `os.path`
  strings, not `pathlib`; accept `os.PathLike` at the API boundary with
  `os.fspath`. Keep the public API compatible with 1.0.x.
- Classes use `__slots__` (including `__dict__` and `__weakref__`) and must keep
  loading pickles made by seqparse 1.0.x.

## Tests

- Tests live in `seqparse/test/` (unittest style, run with pytest) and are not
  shipped in the wheel.
- Paths: library output uses native separators. Compare paths in tests with
  separators normalized to "/" (see `_posix` in `test_regressions.py`), never
  against hardcoded "/" strings. `test_windows_paths.py` simulates Windows
  path rules on any OS.
- Pickle fixtures must not contain OS-specific `os.stat_result` fields;
  `test_legacy_pickles_are_portable` checks that.
- `test_readme.py` doctests the Python examples in `README.md`, so README
  examples must be real output.

## Git and releases

- Commit and push only when asked. Show the commit message for approval first.
- Commit message format: a subject of at most 60 characters, then at most 8
  bullets ordered by impact. No Co-Authored-By line.
- Never change the version (`seqparse/__init__.py`) unless asked. Add
  user-visible changes to the `## Unreleased` section of `CHANGES.md` as you
  make them; it gets renamed when releasing.
