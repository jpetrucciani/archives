#!/usr/bin/env python
"""
pip setup file
"""
import os
import re
from setuptools import setup, find_packages


REQUIRED = ["click>=7.0", "typed-ast>=1.4.0", "radon>=3.0.3"]
LIBRARY = "archives"


with open("README.md") as readme:
    LONG_DESCRIPTION = readme.read()


def find_version(*file_paths):
    """
    This pattern was modeled on a method from the Python Packaging User Guide:
        https://packaging.python.org/en/latest/single_source_version.html
    We read instead of importing so we don't get import errors if our code
    imports from dependencies listed in install_requires.
    """
    base_module_file = os.path.join(*file_paths)
    with open(base_module_file) as module_file:
        base_module_data = module_file.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", base_module_data, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name=LIBRARY,
    version=find_version("archives", "globals.py"),
    description=("a new way to do python code documentation"),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    entry_points={"console_scripts": ["archives=archives.archives:archives"]},
    zip_safe=False,
)
