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
        # flags
        self.verbose = False
        self.quiet = False
        self.ignore_exceptions = False
        self.stats = False

        # disables
        self.disable_list: List[str] = []

        # output options
        self.format = "flake8"
        self.module_rules: List = []
        self.class_rules: List = []
        self.function_rules: List = []

        # object counters
        self.module_count = 0
        self.class_count = 0
        self.function_count = 0

        # object no lint counters
        self.module_nolint_count = 0
        self.class_nolint_count = 0
        self.function_nolint_count = 0


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
