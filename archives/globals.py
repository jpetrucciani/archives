"""
@author jacobi petrucciani
@desc global vars for archives
"""
import sys
from typed_ast import ast3  # noqa


__version__ = "0.11"


PY_VERSION = sys.version_info
# if PY_VERSION[0] >= 3 and PY_VERSION[1] >= 8:
#     # we should use the built in ast if python 3.8 or higher
#     # see https://github.com/python/typed_ast#python-38
#     import ast as ast3
# else:
#     # use the forked typed version
#     from typed_ast import ast3  # type: ignore # noqa


DEFAULT_EXCLUDES_LIST = [
    r"\.eggs",
    r"\.git",
    r"\.hg",
    r"\.mypy_cache",
    r"\.nox",
    r"\.tox",
    r"\.venv",
    r"env",
    r"_build",
    r"buck-out",
    r"build",
    r"dist",
]
DEFAULT_EXCLUDES = r"/(" + "|".join(DEFAULT_EXCLUDES_LIST) + ")/"
DEFAULT_INCLUDES = r"\.pyi?$"


DEFAULT_ARG_IGNORE = ["self", "cls"]

FORMATS = {
    "flake8": "{path}:{line}:{column}: {code} {text}",
    "pylint": "{path}:{line}: [{code}] {text}",
}
