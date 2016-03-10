#!/usr/bin/env python


from setuptools import setup, find_packages, Extension

VERSION = (0, 4, 0)
VERSION_STR = ".".join([str(x) for x in VERSION])

setup(
    name='bsread',
    version=VERSION_STR,
    description="BSREAD for Python",
    # long_description=open('Readme.rst', 'r').read(),
    long_description="BSREAD for Python",
    author='Paul Scherrer Institute',
    author_email='psi@psi.ch',
    url='https://git.psi.ch/sf_daq/bsread_python',
    packages=['bsread', 'bsread.handlers'],
    requires=['mflow', 'numpy', 'pyzmq'],

)
