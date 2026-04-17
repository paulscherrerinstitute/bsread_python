#!/usr/bin/env python
import os
from setuptools import find_packages, setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="psi-bsread",
    version='2.0.2',
    url="https://github.com/paulscherrerinstitute/bsread_python",
    description="bsread for Python",
    author="Paul Scherrer Institute",
    license="GNU GPLv3",
    install_requires=["psi-mflow", "click", "numpy", "pyzmq", "requests", "lz4", "bitshuffle"],
    packages=find_packages(),
    long_description=read('Readme.md'),
    long_description_content_type="text/markdown",
)



