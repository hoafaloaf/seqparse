# seqparse.py

[![Build Status](https://travis-ci.org/hoafaloaf/seqparse.svg?branch=master)](https://travis-ci.org/hoafaloaf/seqparse) [![Coverage Status](https://coveralls.io/repos/github/hoafaloaf/seqparse/badge.svg)](https://coveralls.io/github/hoafaloaf/seqparse) [![Code Health](https://landscape.io/github/hoafaloaf/seqparse/develop/landscape.svg?style=flat)](https://landscape.io/github/hoafaloaf/seqparse)


A nifty way to list your file sequences.

## Overview

Coming soon.

## Roadmap

1. v0.4.0
    1. **COMPLETED v0.4.0a1:** Create `regex.RegexMixin` class, add to
    `FrameChunk`, `FrameSequence`, `FileSequence`.
    1. **COMPLETED v0.4.0a1:** Implement `FileSequence` class.
    1. **COMPLETED v0.4.0a2:** Use the `FileSequence` class' built in
    functionality to replace the `Seqparse._iterate_over_sequence` method.
    1. **COMPLETED v0.4.0a2:** Make sure we can measure equality between
    `FrameChunk`, `FrameSequence`, and `FileSequence` instances.
    1. **COMPLETED v0.4.0a3:** Add ability for `seqls` to only output file
    sequences.
    1. **COMPLETED v0.4.0a3:** Add ability for `seqls` to output inverted file
    sequences.
1. v0.5.0
    1. Add ability to calculate/output total size of file sequences
    (`FileSequence/Seqparse`).
    1. Add ability to calculate/output total size of singletons (`Seqparse`).
1. v0.6.0
    1. Make `Seqparse.sequences` iterable (and possible add a containment
    test).
    1. Make `Seqparse.singletons` iterable (and possible add a containment
    test).
1. v0.7.0
    1. Implement tree-style output for `Seqparse.output`.
    1. Add support for negative frame numbers.
    1. Add support negative frame increments (read only).
1. v0.8.0
    1. ***DOCUMENT ALL THE THINGS!***
1. v1.0.0
    1. Release.
