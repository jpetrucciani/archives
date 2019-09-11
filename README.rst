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


.. image:: https://img.shields.io/badge/docstyle-archives-lightblue.svg
   :target: https://github.com/jpetrucciani/archives
   :alt: Documentation style: archives


**archives** is a new style of python code documentation, as well as a linter for the documentation itself. It can help you ensure that your docstrings in your classes and functions stay up to date, and that they adequately explain their purpose, arguments, and return value.


.. image:: https://i.kym-cdn.com/entries/icons/original/000/023/967/obiwan.jpg
    :width: 100 %
    :alt: Perhaps the archives are incomplete

Features
--------

- linter for docstrings (work in progress, but usable)
- (coming soon) documentation generator

Usage
-----

Installation
^^^^^^^^^^^^

.. code-block:: bash

  pip install archives

Run the Linter
^^^^^^^^^^^^^^
.. code-block:: bash

  # run archives (on itself!)
  archives archives.py

  #> archives.py:846:0: F104 function 'path_empty' missing @ret tag
  #>
  #> Impossible! Perhaps your archives are incomplete?
  #> 1 issues found.

  # list rules!
  archives --list-rules

  # disable rules!
  archives --disable M100 .

  # different formats for output! defaults to flake8
  archives --format pylint archives.py


Testing
-------

Tests can be run with tox!

.. code-block:: bash

   # run tests
   tox

   # only one version of python
   tox -e py36


Todo
----
- more rules
- better system for multi-check rules
- more output formats
- potentially spell-checking inside desc?
- documentation generator
- tests
- ignore @ret if None return type
