#!/usr/bin/env python


from setuptools import setup, find_packages, Extension

VERSION = (0, 0, 1)
VERSION_STR = ".".join([str(x) for x in VERSION])

setup(
    name='bsread',
    version=VERSION_STR,
    description="BSREAD for Python",
    # long_description=open('Readme.rst', 'r').read(),
    long_description="BSREAD for Python",
    author='PSI',
    author_email='im@psi.ch',
    url='https://github.psi.ch/projects/ST/repos/bsread_python/browse',
    packages=['bsread', 'bsread.handler'],

)
