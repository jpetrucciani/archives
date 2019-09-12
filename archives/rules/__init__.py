"""
@author jacobi petrucciani
@desc archives rules submodule
"""
from typing import Union
from archives.models.rules import Rule
from archives.models.python import Class, Function, Module
from archives.globals import ast3


def no_docstring(obj: Union[Class, Function, Module]) -> bool:
    """
    @cc 1
    @desc no docstring test
    @arg obj: a class, function, or module to check
    @ret true if the obj has no docstring
    """
    return not obj.doc


def no_desc(obj: Union[Class, Function, Module]) -> bool:
    """
    @cc 1
    @desc no description test
    @arg obj: a class, function, or module to check
    @ret true if the obj has no @desc tag
    """
    return not obj.doc or not obj.doc.desc


def no_author(module: "Module") -> bool:
    """
    @cc 1
    @desc no author test
    @arg module: a module to check
    @ret true if the module has no @author tag
    """
    return not module.doc or not module.doc.author


def no_cc(obj: "Function") -> bool:
    """
    @cc 1
    @desc no cyclomatic complexity test
    @arg obj: a function to check
    @ret true if the function does not have a @cc tag
    """
    return not obj.doc or obj.doc.cc == -1


def wrong_cc(obj: "Function") -> bool:
    """
    @cc 1
    @desc incorrect cyclomatic complexity test
    @arg obj: a function to check
    @ret true if the function has an incorrect @cc tag
    """
    return not obj.doc or not obj.doc.cc or obj.doc.cc != obj.complexity


def no_ret(function: "Function") -> bool:
    """
    @cc 2
    @desc no return tag test
    @arg function: a function to check
    @ret true if the function does not have a @ret tag
    """
    returns_none = bool(function.return_typed and not function.returns)
    if returns_none:
        return False
    return not function.doc or not function.doc.ret


def no_ret_type(function: "Function") -> bool:
    """
    @cc 1
    @desc no return type test
    @arg function: a function to check
    @ret true if the function does not have a declared return type
    """
    return not function.return_typed


def unnecessary_ret(function: "Function") -> bool:
    """
    @cc 1
    @desc unnecessary return tag test
    @arg function: a function to check
    @ret true if the function has a @ret tag but doesn't need one
    """
    returns_none = bool(
        function.returns
        and isinstance(function.returns, ast3.NameConstant)
        and not function.returns.value
    )
    return bool(returns_none and function.doc and function.doc.ret)


def nop(obj: Union[Class, Function, Module]) -> bool:
    """
    @cc 1
    @desc a no-op check to allow for issues that can be manually added
    @arg obj: a class, function, or module to check
    @ret always True
    """
    return True


MODULE_RULES = [
    Rule("M100", "module '{name}' missing docstring", no_docstring),
    Rule("M101", "module '{name}' missing @desc tag", no_desc),
    Rule("M102", "module '{name}' missing @author tag", no_author),
]
CLASS_RULES = [
    Rule("C100", "class '{name}' missing docstring", no_docstring),
    Rule("C101", "class '{name}' missing @desc tag", no_desc),
]
FUNCTION_RULES = [
    Rule("F100", "function '{name}' missing docstring", no_docstring),
    Rule("F101", "function '{name}' missing @desc tag", no_desc),
    Rule("F102", "function '{name}' missing @cc tag (cc: {cc})", no_cc),
    Rule(
        "F103",
        "function '{name}' mismatched @cc tag ({doc_cc}, expected {cc})",
        wrong_cc,
    ),
    Rule("F104", "function '{name}' missing @ret tag", no_ret),
    Rule("F105", "function '{name}' has unnecessary @ret tag", unnecessary_ret),
    Rule("F106", "function '{name}' has no return type", no_ret_type),
]
MISSING_ARG = Rule("A100", "function '{name}' missing @arg for '{arg}'", nop)
UNEXPECTED_ARG = Rule("A101", "function '{name}' unexpected @arg for '{arg}'", nop)
UNTYPED_ARG = Rule("A102", "function '{name}' has untyped arg '{arg}'", nop)
