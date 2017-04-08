#!python
"""Set up the seqparse module."""

# Standard Libraries
import codecs
import os
import re
import sys

# Third Party Libraries
import setuptools
from setuptools import find_packages, setup

import seqparse

if sys.version_info < (2, 7):
    sys.exit('Sorry, Python < 2.7 is not supported')

HERE = os.path.abspath(os.path.dirname(__file__))

###############################################################################

NAME = "seqparse"
KEYWORDS = ["command-line", "file", "sequence"]
DOWNLOAD_URL = 'https://github.com/hoafaloaf/seqparse/archive/v{ver}.tar.gz'

CLASSIFIERS = [
    'Development Status :: 4 - Beta', 'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing'
]

EXTRAS_REQUIRE = dict()
INSTALL_REQUIRES = ["future", "humanize", "six"]
TEST_REQUIRES = ["coverage < 4.4a0", "nose", "pylint"]

if int(setuptools.__version__.split(".", 1)[0]) < 18:
    assert "bdist_wheel" not in sys.argv, "setuptools 18 required for wheels."

    # For legacy setuptools + sdist.
    if sys.version_info[0:2] < (3, 3):
        INSTALL_REQUIRES.append("mock >= 1.1")
    if sys.version_info[0:2] < (3, 5):
        INSTALL_REQUIRES.append("scandir >= 1.1")
else:
    EXTRAS_REQUIRE[":python_version < '3.5'"] = ["scandir >= 1.1"]
    TEST_REQUIRES.append("mock >= 1.1")

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
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta),
        META_FILE,
        re.M)
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(
        name=NAME,
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
        setup_requires=['nose>=1.0'],
        test_suite='nose.collector',
        tests_require=TEST_REQUIRES,
        url=find_meta("uri"),
        version=seqparse.__version__,
        zip_safe=False)
