"""
this is the module docstring
"""
import this


def bad_function(variable):
    return 4


def good_function(text: str, meme: int = 420) -> float:
    """this has a docstring"""
    return 4.20


def nested_function(text: str) -> None:
    """this is nested"""

    def sub_function(text: str) -> None:
        """this doesn't really do anything"""


class BadClass:
    """lame"""

    def func(variable):
        return 4


class GoodClass:
    """good class"""

    def func(self, variable: str, meme: int = 420, another: str = "") -> float:
        """
        @desc this function returns a memey number
        @arg variable this variable means nothing
        @arg meme this kwarg is default to 420
        @link test http://http.rip
        @ret the meme number
        """
        return 4.20
