## Stuff to do:

1. Add support for decoding frame sequences (as output by the seqparse module).
1. Add support for negative frame numbers.
1. Add support negative frame increments (read only).
1. Add `FrameChunk` set-like functionality
1. Implement `OutputSequence` class.
1. Add ability to *invert* frame sequences (ie, find missing frames).
1. Make sure that everything that should be iterable **is** iterable.
1. Add ability to calculate/output total size of file sequences and
   singletons.
1. Add ability to only output singletons/file sequences.
1. Add glob-like capabilities when reading from disk (ie, "dog.*" or
   individual frames).
