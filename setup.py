#!/usr/bin/env python

from setuptools import find_packages, setup


setup(
    name="bsread",
    version="1.6.2",
    url="https://github.com/paulscherrerinstitute/bsread_python",
    description="bsread for Python",
    author="Paul Scherrer Institute",
    requires=["bitshuffle", "click", "mflow", "numpy", "pyzmq"],
    packages=find_packages()
)



