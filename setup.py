#!/usr/bin/env python


from setuptools import setup

VERSION = (1, 6, 2)
VERSION_STR = ".".join([str(x) for x in VERSION])

setup(
    name='bsread',
    version=VERSION_STR,
    description="BSREAD for Python",
    long_description="BSREAD for Python",
    author='Paul Scherrer Institute',
    author_email='daq@psi.ch',
    url='https://git.psi.ch/sf_daq/bsread_python',
    packages=['bsread', 'bsread.handlers', 'bsread.cli', 'bsread.data'],
    requires=['mflow', 'bitshuffle', 'numpy', 'pyzmq', 'click'],
    zip_safe=False,

)
