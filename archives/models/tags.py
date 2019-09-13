"""
@author jacobi petrucciani
@desc tags for archives
"""
import re
from typing import Pattern


CHAR = "@"
EOL = r"(?:\n|\Z)"
SPACE = r"(?:\s+)"
ALNUM = r"([a-zA-Z0-9_]+)"
ANY = r"(.+)"


def base_tag(name: str) -> Pattern:
    """
    @cc 1
    @desc return a basic tag type
    @arg name: the name that will determine the tag
    @ret a compiled regex pattern for this tag
    """
    return re.compile(rf"(?:{CHAR}{name}):?{SPACE}{ANY}{EOL}")


def base_int_tag(name: str) -> Pattern:
    """
    @cc 1
    @desc return a basic tag type that only accepts an integer
    @arg name: the name that will determine the tag
    @ret a compiled regex pattern for this tag
    """
    return re.compile(rf"(?:{CHAR}{name}):?{SPACE}([0-9]+){EOL}")


def base_arg_tag(name: str) -> Pattern:
    """
    @cc 1
    @desc return a basic tag type that allows for two args
    @arg name: the name that will determine the tag
    @ret a compiled regex pattern for this tag
    """
    return re.compile(rf"(?:{CHAR}{name}){SPACE}{ALNUM}:?{SPACE}{ANY}{EOL}")


class Tag:
    """
    @desc tag namespace
    """

    AUTHOR = base_tag("author")
    CC = base_int_tag("cc")
    DESC = base_tag("desc")
    TODO = base_tag("todo")
    NOTE = base_tag("note")
    WARN = base_tag("warn")
    RETURN = base_tag("ret")
    ARG = base_arg_tag("arg")
    LINK = base_arg_tag("link")
