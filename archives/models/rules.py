"""
@author jacobi petrucciani
@desc rules and issues models
"""
from typing import Callable, Dict, Union
from archives.models.python import Class, Function, Module


class Rule:
    """
    @desc a rule for an issue with the archives
    """

    def __init__(self, code: str, desc: str, check: Callable) -> None:
        """
        @cc 1
        @desc issue constructor
        @arg code: the error code for the rule
        @arg desc: the description string
        @arg check: a function to check if this rule is broken
        """
        self.code = code
        self.check = check
        self.desc = desc


class Issue:
    """
    @desc an instance of a Rule being flagged
    """

    def __init__(
        self, rule: Rule, obj: Union[Class, Function, Module], extra: Dict = None
    ) -> None:
        """
        @cc 1
        @desc constructor for issue
        @arg rule: an instance of the rule being broken
        @arg obj: either a class, function, or module that breaks the rule
        @arg extra: extra data to pass to the issue description template
        """
        self.rule = rule
        self.obj = obj
        self.line = 0 if isinstance(obj, Module) else obj.line
        self.column = 0 if isinstance(obj, Module) else obj.column
        self.extra = extra or {}

    def __str__(self) -> str:
        """
        @cc 1
        @desc string dunder method
        @ret the string representation of this Issue
        """
        return f"<Issue[{self.rule.code}] {self.obj}>"

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repl representation of this Issue
        """
        return self.__str__()
