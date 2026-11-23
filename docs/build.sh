#!/bin/sh
# Build the API documentation (needs the "docs" extra: pip install ".[docs]").
# Usage: sh docs/build.sh [output-directory]   (default: site)
#
# pdoc honors __all__, and the package's __all__ lists no submodules, so the
# public modules are named here; keep this list in step with
# seqparse/test/test_public_api.py.
set -eu
exec pdoc \
    seqparse \
    seqparse.cli.seqls \
    seqparse.cli.seqtransfer \
    seqparse.containers \
    seqparse.files \
    seqparse.regex \
    seqparse.seqparse \
    seqparse.sequences \
    seqparse.transfer \
    --docformat google \
    --output-directory "${1:-site}"
