#!/usr/bin/env python
"""
pip setup file
"""
from setuptools import setup, find_packages


REQUIRED = ["click>=7.0"]
LIBRARY = "archives"


with open("README.rst") as readme:
    LONG_DESCRIPTION = readme.read()


setup(
    name=LIBRARY,
    version="0.3",
    description=("a new way to do python code documentation"),
    long_description=LONG_DESCRIPTION,
    author="Jacobi Petrucciani",
    author_email="jacobi@mimirhq.com",
    url="https://github.com/jpetrucciani/{}.git".format(LIBRARY),
    download_url="https://github.com/jpetrucciani/{}.git".format(LIBRARY),
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
