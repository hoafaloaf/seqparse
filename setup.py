#!python
"""Set up the seqparse module."""

# Standard Libraries
import codecs
import os
import sys

# Third Party Libraries
from setuptools import find_packages, setup

import seqparse

DOWNLOAD_URL = 'https://github.com/hoafaloaf/seqparse/archive/v{ver}.tar.gz'


def _read_file(file_name):
    """Read a file and return its contents."""
    contents = ""
    if os.path.exists(file_name):
        with open(os.path.join(os.path.dirname(__file__), file_name)) as ff:
            contents = ff.read()
    return contents


install_requires = list()
for line in _read_file('requirements.txt').split('\n'):
    if not (line.startswith("#") or line.startswith('-')):
        install_requires.append(line.replace('==', '>='))

test_requires = [
    "coverage < 4.4a0", "mock >= 1.1; python_version < '3.3'", "nose >= 1.0",
    "pylint >= 1.3"
]

if sys.version_info < (2, 7):
    sys.exit('Sorry, Python < 2.7 is not supported')

with codecs.open('README.rst', 'r', 'utf-8') as fd:
    setup(
        name='seqparse',
        author='Geoff Harvey',
        author_email='hoafaloaf@gmail.com',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Text Processing'
        ],
        description='A nifty way to parse your file sequences.',
        download_url=DOWNLOAD_URL.format(ver=seqparse.__version__),
        entry_points={
            'console_scripts': ['seqls = seqparse.cli.seqls:run_main']
        },
        install_requires=install_requires,
        keywords='command-line file sequence',
        license='MIT',
        long_description=fd.read(),
        packages=find_packages(exclude=['*test']),
        setup_requires=['nose>=1.0'],
        test_suite='nose.collector',
        tests_require=test_requires,
        url='http://github.com/hoafaloaf/seqparse',
        version=seqparse.__version__,
        zip_safe=False)
