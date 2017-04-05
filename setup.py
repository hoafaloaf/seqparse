#!python
"""Set up the seqparse module."""

# Standard Libraries
import sys

# Third Party Libraries
from setuptools import find_packages, setup

if sys.version_info < (2, 7):
    sys.exit('Sorry, Python < 2.7 is not supported')


def readme():
    """Pass back the package's README.md."""
    with open('README.md') as ff:
        return ff.read()


setup(
    name='seqparse',
    author='Geoff Harvey',
    author_email='hoafaloaf@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing'
    ],
    description='A nifty way to parse your file sequences.',
    entry_points={
        'console_scripts': ['seqls = seqparse.cli.seqls:_entry_point']
    },
    install_requires=['humanize', 'scandir;python_version<"3.5"'],
    keywords='command-line file sequence',
    license='MIT',
    packages=find_packages(exclude=['*test']),
    test_suite='nose.collector',
    tests_require=['coverage', 'nose', 'pylint'],
    url='http://github.com/hoafaloaf/seqparse',
    version='0.6.0',
    zip_safe=False)
