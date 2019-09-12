"""
@author jacobi petrucciani
@desc tags for archives
"""
import re


class Tag:
    """
    @desc tag namespace
    """

    CHAR = "@"
    EOL = r"(?:\n|\Z)"
    AUTHOR = re.compile(rf"(?:{CHAR}author):?(?:\s+)(.+){EOL}")
    CC = re.compile(rf"(?:{CHAR}cc):?(?:\s+)([0-9]+){EOL}")
    DESC = re.compile(rf"(?:{CHAR}desc):?(?:\s+)(.+){EOL}")
    RETURN = re.compile(rf"(?:{CHAR}ret):?(?:\s+)(.+){EOL}")
    ARG = re.compile(rf"(?:{CHAR}arg)(?:\s+)([a-zA-Z0-9_]+):?(?:\s+)(.+){EOL}")
    LINK = re.compile(rf"(?:{CHAR}link)(?:\s+)([a-zA-Z0-9_]+):?(?:\s+)(.+){EOL}")
