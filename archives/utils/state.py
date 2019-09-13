"""
@author jacobi petrucciani
@desc click state related handling
"""
import click
from typing import List


class State:
    """
    @desc state object for click
    """

    def __init__(self) -> None:
        """
        @cc 1
        @desc state constructor
        """
        self.verbose = False
        self.quiet = False
        self.disable_list: List[str] = []
        self.format = "flake8"
        self.module_rules: List = []
        self.class_rules: List = []
        self.function_rules: List = []
        self.ignore_exceptions = False


def get_state() -> State:
    """
    @cc 2
    @desc gets the current state of the click app
    @ret the current click state object
    """
    try:
        return click.get_current_context().ensure_object(State)
    except RuntimeError:
        # this allows us to use archives programmatically
        return State()
