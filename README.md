# seqparse.py

[![Build Status](https://travis-ci.org/hoafaloaf/seqparse.svg?branch=master)](https://travis-ci.org/hoafaloaf/seqparse) [![Coverage Status](https://coveralls.io/repos/github/hoafaloaf/seqparse/badge.svg)](https://coveralls.io/github/hoafaloaf/seqparse) [![Code Health](https://landscape.io/github/hoafaloaf/seqparse/develop/landscape.svg?style=flat)](https://landscape.io/github/hoafaloaf/seqparse)


A nifty way to list your file sequences.

## Overview

Coming soon.

## Stuff to do

1. **IN PROGRESS** Add ability to *invert* frame sequences (ie, find missing
   frames).
1. Implement `FileSequence` class, use built in functionality to replace the
   `Seqparse._iterate_over_sequence` method.
1. Make `Seqparse.sequences` iterable (and possible add a containment test).
1. Make `Seqparse.singletons` iterable (and possible add a containment test).
1. Add ability to calculate/output total size of file sequences.
1. Add ability to calculate/output total size of singletons.
1. Add support for negative frame numbers.
1. Add support negative frame increments (read only).
1. Add ability to only output singletons/file sequences.
1. Implement tree-style output for `Seqparse.output`.
