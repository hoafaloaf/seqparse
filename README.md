# seqparse.py

[![Build Status](https://travis-ci.org/hoafaloaf/seqparse.svg?branch=master)](https://travis-ci.org/hoafaloaf/seqparse) [![Coverage Status](https://coveralls.io/repos/github/hoafaloaf/seqparse/badge.svg)](https://coveralls.io/github/hoafaloaf/seqparse) [![Code Health](https://landscape.io/github/hoafaloaf/seqparse/develop/landscape.svg?style=flat)](https://landscape.io/github/hoafaloaf/seqparse)


A nifty way to list your file sequences.

## Overview

Coming soon.

## Roadmap

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

## TODO

1. *feature/add-stat-query-ability*: Create mechanism on the `FrameSequence`
   class to query disk `stat` data post-creation. Probably allow it to re-scan
   for changed frames and/or newly created, previously missing frames (see:
   `mtime` and `ctime`).
