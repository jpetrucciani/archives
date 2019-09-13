# archives: a new way to do python code documentation

[![image](https://travis-ci.org/jpetrucciani/archives.svg?branch=master)](https://travis-ci.org/jpetrucciani/archives)
[![PyPI
version](https://badge.fury.io/py/archives.svg)](https://badge.fury.io/py/archives)
[![Code style:
black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Python 3.6+
supported](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Documentation style:
archives](https://img.shields.io/badge/docstyle-archives-lightblue.svg)](https://github.com/jpetrucciani/archives)

**archives** is a new style of python code documentation, as well as a
linter for the documentation itself. It can help you ensure that your
docstrings in your classes and functions stay up to date, and that they
adequately explain their purpose, arguments, and return value.

![Perhaps the archives are
incomplete](https://i.kym-cdn.com/entries/icons/original/000/023/967/obiwan.jpg)

## Features

  - linter for docstrings (work in progress, but usable\!)
  - (coming soon) documentation generator

## Usage

### Installation

``` bash
pip install archives
```

### Run the Linter

``` bash
# run archives (on itself!)
archives archives/

# archives.py:846:0: F104 function 'path_empty' missing @ret tag
#
# Impossible! Perhaps your archives are incomplete?
# 1 issues found.

# list tags!
archives --list-tag

# @arg    describe an argument of a function
# @author denote the author of a module/class/function
# @cc     denote the complexity of a function
# @desc   describe a module/class/function
# @link   add a link to the generated documentation
# @nodoc  disable this module/class/function in the documentation
# @nolint disable archives linting in this module/class/function
# @note   add a note to a module/class/function
# @ret    describe the return value of a function
# @todo   tag something as a todo
# @warn   add a warning to a module/class/function

# list rules!
archives --list-rules


# disable rules!
archives --disable M100 .

# different formats for output! defaults to flake8
archives --format pylint archives.py
```

## Testing

Tests can be run with tox\!

``` bash
# run tests
tox

# only one version of python
tox -e py36
```

## Todo

  - more rules
  - better system for multi-check rules
  - more output formats
  - potentially spell-checking inside desc?
  - documentation generator
  - tests