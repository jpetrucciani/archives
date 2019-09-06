archives: a new way to do python code documentation
===================================================

.. image:: https://travis-ci.org/jpetrucciani/archives.svg?branch=master
    :target: https://travis-ci.org/jpetrucciani/archives


.. image:: https://badge.fury.io/py/archives.svg
   :target: https://badge.fury.io/py/archives
   :alt: PyPI version


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black
   :alt: Code style: black


.. image:: https://img.shields.io/badge/python-3.6+-blue.svg
   :target: https://www.python.org/downloads/release/python-360/
   :alt: Python 3.6+ supported


**archives** is a new style of python code documentation, as well as a linter for the documentation itself. It can help you ensure that your docstrings in your classes and functions stay up to date, and that they adequately explain their purpose, arguments, and return value.


.. image:: https://i.kym-cdn.com/entries/icons/original/000/023/967/obiwan.jpg
    :width: 50 %
    :alt: Perhaps the archives are incomplete

Features
--------

- (coming soon) linter for docstrings
- (coming soon) documentation generator

Usage
-----

Installation
^^^^^^^^^^^^

.. code-block:: bash

   pip install archives


Testing
-------

Tests can (almost) be run with tox!

.. code-block:: bash

   # run tests
   tox


Todo
----
- more rules
- better system for multi-check rules
- more output formats
- documentation generator
- tests
