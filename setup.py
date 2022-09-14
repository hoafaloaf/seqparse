"""Set up the seqparse module."""

import codecs
import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    """
    Build an absolute path from *parts*, return contents of resulting file.

    Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as fd:
        return fd.read()

LONG_DESCRIPTION = read(os.path.join(HERE, 'README.rst'))


if __name__ == '__main__':
    setup(long_description=read(os.path.join(HERE, 'README.rst')),
          packages=find_packages(exclude=['*test']),
          test_suite='seqparse.test')
