#!/usr/bin/env python
"""
pip setup file
"""
from setuptools import setup, find_packages


with open("README.rst") as readme:
    LONG_DESCRIPTION = readme.read()


REQUIRED = ["click>=7.0"]

setup(
    name="archives",
    version="0.2",
    description=("a new way to do python code documentation"),
    long_description=LONG_DESCRIPTION,
    author="Jacobi Petrucciani",
    author_email="jacobi@mimirhq.com",
    url="https://github.com/jpetrucciani/archives.git",
    download_url="https://github.com/jpetrucciani/archives.git",
    license="MIT",
    packages=find_packages(),
    install_requires=REQUIRED,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    entry_points={"console_scripts": ["archives=archives:archives"]},
    zip_safe=False,
)
