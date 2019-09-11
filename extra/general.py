"""
this is the module docstring
"""
import this
from typing import Dict, List, Union


def bad_function(variable):
    return 4


def good_function(text: str, meme: int = 42) -> float:
    """this has a docstring"""
    return 4.2


def nested_function(text: str) -> None:
    """this is nested"""

    def sub_function(text: str) -> None:
        """this doesn't really do anything"""


def function_with_weird_types(
    data: Union[List[str], Dict, str]
) -> Union[int, float, str]:
    """"""
    return 42


class BadClass:
    """lame"""

    def func(variable):
        return 4


class GoodClass:
    """good class"""

    def func(self, variable: str, meme: int = 42, another: str = "") -> float:
        """
        @desc this function returns a memey number
        @arg variable this variable means nothing
        @arg meme this kwarg is default to 42
        @link test http://http.rip
        @ret the meme number
        """
        return 4.2
