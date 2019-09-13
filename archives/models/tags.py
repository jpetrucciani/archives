"""
@author jacobi petrucciani
@desc tags for archives
"""
import re
from typing import List, Pattern


CHAR = "@"
EOL = r"(?:\n|\Z)"
SPACE = r"(?:\s+)"
ALNUM = r"([a-zA-Z0-9_]+)"
ANY = r"(.+)"


class Tag:
    """
    @desc an instance of a tag
    """

    def __init__(self, name: str, regex: Pattern, desc: str) -> None:
        """
        @cc 1
        @desc tag constructor
        @arg name: a name for this tag
        @arg regex: a regex pattern to use for this tag
        @arg desc: a description for this tag
        """
        self.name = name
        self.regex = regex
        self.desc = desc


def tag(name: str, desc: str) -> Tag:
    """
    @cc 1
    @desc return a basic tag type
    @arg name: the name that will determine the @tag
    @arg desc: the description for this tag
    @ret a compiled regex pattern for this tag
    """
    return Tag(name, re.compile(rf"({CHAR}{name})"), desc)


def str_tag(name: str, desc: str) -> Tag:
    """
    @cc 1
    @desc return a basic tag type that captures the rest of the line
    @arg name: the name that will determine the @tag
    @arg desc: the description for this tag
    @ret a compiled regex pattern for this tag
    """
    return Tag(name, re.compile(rf"(?:{CHAR}{name}):?{SPACE}{ANY}{EOL}"), desc)


def int_tag(name: str, desc: str) -> Tag:
    """
    @cc 1
    @desc return a basic tag type that only captures an integer
    @arg name: the name that will determine the @tag
    @arg desc: the description for this tag
    @ret a compiled regex pattern for this tag
    """
    return Tag(name, re.compile(rf"(?:{CHAR}{name}):?{SPACE}([0-9]+){EOL}"), desc)


def arg_tag(name: str, desc: str) -> Tag:
    """
    @cc 1
    @desc return a basic tag type that allows for two args, a name and a value
    @arg name: the name that will determine the @tag
    @arg desc: the description for this tag
    @ret a compiled regex pattern for this tag
    """
    return Tag(
        name, re.compile(rf"(?:{CHAR}{name}){SPACE}{ALNUM}:?{SPACE}{ANY}{EOL}"), desc
    )


class Tags:
    """
    @desc tag namespace
    """

    all_types = "module/class/function"

    # general tags
    ARG = arg_tag("arg", f"describe an argument of a function")
    AUTHOR = str_tag("author", f"denote the author of a {all_types}")
    CC = int_tag("cc", f"denote the complexity of a function")
    DESC = str_tag("desc", f"describe a {all_types}")
    RETURN = str_tag("ret", f"describe the return value of a function")
    TODO = str_tag("todo", f"tag something as a todo")

    # documentation tags
    LINK = arg_tag("link", f"add a link to the generated documentation")
    NOTE = str_tag("note", f"add a note to a {all_types}")
    WARN = str_tag("warn", f"add a warning to a {all_types}")

    # flag tags
    NO_DOC = tag("nodoc", f"disable this {all_types} in the documentation")
    NO_LINT = tag("nolint", f"disable archives linting in this {all_types}")

    @classmethod
    def all(cls) -> List[Tag]:
        """
        @cc 1
        @desc get all tags in this enum
        @ret a list of the tag objects
        """
        return sorted(
            [
                cls.__dict__[x]
                for x in dir(cls)
                if not x.startswith("_") and isinstance(cls.__dict__[x], Tag)
            ],
            key=lambda x: x.name,
        )
