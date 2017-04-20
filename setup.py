#!/usr/bin/env python


from setuptools import setup

VERSION = (0, 8, 7)
VERSION_STR = ".".join([str(x) for x in VERSION])

setup(
    name='bsread',
    version=VERSION_STR,
    description="BSREAD for Python",
    long_description="BSREAD for Python",
    author='Paul Scherrer Institute',
    author_email='daq@psi.ch',
    url='https://git.psi.ch/sf_daq/bsread_python',
    packages=['bsread', 'bsread.handlers'],
    requires=['mflow', 'bitshuffle', 'numpy', 'pyzmq'],

)
