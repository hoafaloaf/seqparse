#!python
"""Set up the seqparse module."""

# Standard Libraries
import codecs
import os
import re
import sys

import setuptools
from setuptools import find_packages, setup

import seqparse

if sys.version_info < (3, 7):
    sys.exit('Sorry, Python < 3.7 is not supported')

HERE = os.path.abspath(os.path.dirname(__file__))

###############################################################################

NAME = "seqparse"
KEYWORDS = ["command-line", "file", "sequence"]
DOWNLOAD_URL = 'https://github.com/hoafaloaf/seqparse/archive/v{ver}.tar.gz'

CLASSIFIERS = [
    'Development Status :: 4 - Beta', 'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing'
]

EXTRAS_REQUIRE = {}
INSTALL_REQUIRES = ["humanize", "six"]
TEST_REQUIRES = ["coverage", "pylint", "pytest"]

###############################################################################


def read(*parts):
    """
    Build an absolute path from *parts*, return contents of resulting file.

    Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as fd:
        return fd.read()


try:
    META_PATH
except NameError:
    META_PATH = os.path.join(HERE, NAME, "__init__.py")
finally:
    META_FILE = read(META_PATH)

LONG_DESCRIPTION = read(os.path.join(HERE, "README.rst"))


def find_meta(meta):
    """Extract __*meta*__ from META_FILE."""
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE,
        re.M)
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(name=NAME,
          author=find_meta("author"),
          author_email=find_meta("email"),
          classifiers=CLASSIFIERS,
          description=find_meta("description"),
          download_url=DOWNLOAD_URL.format(ver=seqparse.__version__),
          entry_points={
              'console_scripts': ['seqls = seqparse.cli.seqls:run_main']
          },
          extras_require=EXTRAS_REQUIRE,
          install_requires=INSTALL_REQUIRES,
          keywords=KEYWORDS,
          license=find_meta("license"),
          long_description=read(os.path.join(HERE, "README.rst")),
          maintainer_email=find_meta("email"),
          packages=find_packages(exclude=['*test']),
          test_suite='seqparse.test',
          tests_require=TEST_REQUIRES,
          url=find_meta("uri"),
          version=seqparse.__version__,
          zip_safe=False)
