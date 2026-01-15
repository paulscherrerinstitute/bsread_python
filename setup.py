#!/usr/bin/env python

from setuptools import find_packages, setup


setup(
    name="bsread",
    version="2.0.0",
    url="https://github.com/paulscherrerinstitute/bsread_python",
    description="bsread for Python",
    author="Paul Scherrer Institute",
    license="GNU GPLv3",
    requires=["bitshuffle", "click", "mflow", "numpy", "pyzmq"],
    packages=find_packages()
)



