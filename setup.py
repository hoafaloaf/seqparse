#!python
"""Set up the seqparse module."""

# Third Party Libraries
from setuptools import setup


def readme():
    """Pass back the package's README.md."""
    with open('README.md') as ff:
        return ff.read()


setup(
    name='seqparse',
    author='Geoff Harvey',
    author_email='hoafaloaf@gmail.com',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing'
    ],
    description='A nifty way to parse your file sequences.',
    keywords='command-line file sequence',
    include_packaging_data=True,
    install_requires=['scandir'],
    license='MIT',
    packages=['seqparse'],
    scripts=['bin/seqls'],
    test_suite='nose.collector',
    tests_require=['nose'],
    url='http://github.com/hoafaloaf/seqparse',
    version='0.1',
    zip_safe=False)
