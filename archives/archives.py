"""
@author jacobi petrucciani
@desc perhaps the archives are incomplete?
"""
import click
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Set, Tuple
from archives.globals import (
    ast3,
    DEFAULT_INCLUDES,
    DEFAULT_EXCLUDES,
    FORMATS,
    __version__,
)
from archives.models.python import Class, Function, Module
from archives.models.rules import Rule, Issue
from archives.utils.state import get_state, State
from archives.utils.files import find_project_root, path_empty, get_python_files
from archives.utils.text import out, err, msg
from archives.rules import (
    MODULE_RULES,
    CLASS_RULES,
    FUNCTION_RULES,
    MISSING_ARG,
    UNEXPECTED_ARG,
)


def parse_module(filename: str) -> Module:
    """
    @cc 2
    @desc parse a module into our archives' models
    @arg filename: the python file to parse
    @ret a parsed Module object of the given file
    """
    if not os.path.isfile(filename):
        raise Exception("file does not exist")
    contents = ""
    with open(filename, encoding="utf-8", errors="replace") as file_to_read:
        contents += file_to_read.read()
    return Module(ast3.parse(contents), filename)  # type: ignore


def function_lint(
    function: Function,
    class_rules: List[Rule] = None,
    function_rules: List[Rule] = None,
) -> List:
    """
    @cc 8
    @desc function specific lint
    @arg function: the Function object to lint
    @arg class_rules: the altered list of class rules to check
    @arg function_rules: the altered list of function rules to check
    @ret a list of issues found in this function
    """
    state = get_state()
    if not class_rules:
        class_rules = CLASS_RULES
    if not function_rules:
        function_rules = FUNCTION_RULES

    issues = []

    # check this function for rules
    for rule in function_rules:
        if rule.check(function):
            issues.append(Issue(rule, function))

    # check for missing args
    if MISSING_ARG.code not in state.disable_list:
        for arg in function.missing_args:
            issues.append(Issue(MISSING_ARG, function, dict(arg=arg)))

    # check for unexpected args
    if UNEXPECTED_ARG.code not in state.disable_list:
        for arg in function.unexpected_args:
            issues.append(Issue(UNEXPECTED_ARG, function, dict(arg=arg)))

    # check nested classes
    for sub_class in function.classes:
        issues.extend(
            class_lint(
                sub_class, class_rules=class_rules, function_rules=function_rules
            )
        )

    # check all sub functions
    for sub_function in function.functions:
        issues.extend(
            function_lint(
                sub_function, class_rules=class_rules, function_rules=function_rules
            )
        )

    return issues


def class_lint(
    class_def: Class, class_rules: List[Rule] = None, function_rules: List[Rule] = None
) -> List:
    """
    @cc 6
    @desc class specific lint
    @arg class_def: the Class object to lint
    @arg class_rules: the altered list of class rules to check
    @arg function_rules: the altered list of function rules to check
    @ret a list of issues found in this class
    """
    if not class_rules:
        class_rules = CLASS_RULES
    if not function_rules:
        function_rules = FUNCTION_RULES

    issues = []

    # check this class for rules
    for rule in class_rules:
        if rule.check(class_def):
            issues.append(Issue(rule, class_def))

    # check nested classes
    for sub_class in class_def.classes:
        issues.extend(
            class_lint(
                sub_class, class_rules=class_rules, function_rules=function_rules
            )
        )

    # check functions within this class
    for function in class_def.functions:
        issues.extend(
            function_lint(
                function, class_rules=class_rules, function_rules=function_rules
            )
        )

    return issues


def lint(
    module: Module,
    module_rules: List[Rule] = None,
    class_rules: List[Rule] = None,
    function_rules: List[Rule] = None,
) -> List:
    """
    @cc 7
    @desc lint the given module!
    @arg module: the module to lint
    @arg module_rules: the altered list of module rules to check
    @arg class_rules: the altered list of class rules to check
    @arg function_rules: the altered list of function rules to check
    @ret a list of issues found in this module
    """
    if not module_rules:
        module_rules = MODULE_RULES
    if not class_rules:
        class_rules = CLASS_RULES
    if not function_rules:
        function_rules = FUNCTION_RULES
    issues = []

    for rule in module_rules:
        if rule.check(module):
            issues.append(Issue(rule, module))

    for class_def in module.classes:
        issues.extend(
            class_lint(
                class_def, class_rules=class_rules, function_rules=function_rules
            )
        )

    for function in module.functions:
        issues.extend(
            function_lint(
                function, class_rules=class_rules, function_rules=function_rules
            )
        )

    return issues


def archives_lint(ctx: click.Context, sources: Set[Path], state: State) -> None:
    """
    @cc 4
    @desc perform an archives documentation lint
    @arg ctx: the click context of the current run
    @arg sources: the source files to lint
    @arg state: the current click state
    """

    # apply disables
    module_rules = [x for x in MODULE_RULES if x.code not in state.disable_list]
    class_rules = [x for x in CLASS_RULES if x.code not in state.disable_list]
    function_rules = [x for x in FUNCTION_RULES if x.code not in state.disable_list]

    # lint the files
    issues = []
    for file in sources:
        module = parse_module(str(file.absolute()))
        issues.extend(
            lint(
                module,
                module_rules=module_rules,
                class_rules=class_rules,
                function_rules=function_rules,
            )
        )

    for issue in issues:
        obj = issue.obj
        rule = issue.rule
        module = obj if isinstance(obj, Module) else obj.module
        extra_info = dict(name=obj.name)

        # function specific info
        if isinstance(obj, Function):
            extra_info["cc"] = obj.complexity
            if obj.doc:
                extra_info["doc_cc"] = obj.doc.cc

        message = FORMATS[state.format].format_map(
            defaultdict(
                str,
                path=module.path,
                line=issue.line,
                column=issue.column,
                code=rule.code,
                text=rule.desc.format_map(
                    defaultdict(str, **extra_info, **issue.extra)
                ),
            )
        )
        msg(message)
    if not state.quiet:
        if issues:
            trailing_s = "s" if len(issues) != 1 else ""
            err(f"\nImpossible! Perhaps your archives are incomplete?")
            err(f"{len(issues)} issue{trailing_s} found")
        else:
            msg(f"Incredible! It appears that your archives are complete!")
            msg(f"0 issues found")

    ctx.exit(0 if not issues else 1)


def archives_doc(ctx: click.Context, sources: Set[Path], state: State) -> None:
    """
    @cc 1
    @desc perform archives documentation generation
    @arg ctx: the click context of the current run
    @arg sources: the source files to lint
    @arg state: the current click state
    """
    modules = {
        file.parts[-1]: parse_module(str(file.absolute())).serialize()
        for file in sources
    }

    out(modules)
    ctx.exit(0)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--include",
    type=str,
    default=DEFAULT_INCLUDES,
    show_default=True,
    help="regex for files and folders to include",
)
@click.option(
    "--exclude",
    type=str,
    default=DEFAULT_EXCLUDES,
    show_default=True,
    help="regex for files and folders to exclude",
)
@click.option(
    "--format",
    type=click.Choice(FORMATS.keys()),
    default="flake8",
    show_default=True,
    help="format of issue output messages",
)
@click.option(
    "--disable", type=str, default="", help="comma separated list of rules to disable"
)
@click.option("-q", "--quiet", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
@click.option(
    "--list-rules",
    is_flag=True,
    default=False,
    is_eager=True,
    help="list all active rules",
)
@click.option(
    "--doc",
    is_flag=True,
    default=False,
    help="generate documentation for the given sources",
)
@click.version_option(version=__version__)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True
    ),
    is_eager=True,
)
@click.pass_context
def archives(
    ctx: click.Context,
    quiet: bool,
    verbose: bool,
    include: str,
    exclude: str,
    format: str,
    disable: str,
    list_rules: bool,
    doc: bool,
    src: Tuple[str],
) -> None:
    """
    check if your code's archives are incomplete!
    \f
    @cc 7
    @desc the main cli method for archives
    @arg ctx: the click context arg
    @arg quiet: the cli quiet flag
    @arg verbose: the cli verbose flag
    @arg include: a regex for what files to include
    @arg exclude: a regex for what files to exclude
    @arg format: a flag to specify output format for the issues
    @arg disable: a comma separated disable list for rules
    @arg list_rules: a flag to print the list of rules and exit
    @arg doc: a flag to specify if we should generate docs instead of lint
    @arg src: a file or directory to scan for files to lint
    """
    state = ctx.ensure_object(State)
    state.verbose = verbose
    state.quiet = quiet
    state.format = format
    state.disable_list = disable.split(",")

    if list_rules:
        for rule in [
            *MODULE_RULES,
            *CLASS_RULES,
            *FUNCTION_RULES,
            MISSING_ARG,
            UNEXPECTED_ARG,
        ]:
            out(f"{rule.code}: {rule.desc}")
        ctx.exit(0)
    try:
        include_regex = re.compile(include)
    except re.error:
        err(f"invalid regex for include: {include!r}")
        ctx.exit(2)
    try:
        exclude_regex = re.compile(exclude)
    except re.error:
        err(f"invalid regex for exclude: {exclude!r}")
        ctx.exit(2)
    root = find_project_root(src)
    sources: Set[Path] = set()
    path_empty(src, ctx)
    for source in src:
        path = Path(source)
        if path.is_dir():
            sources.update(get_python_files(path, root, include_regex, exclude_regex))
        elif path.is_file() or source == "-":
            # if a file was explicitly given, we don't care about its extension
            sources.add(path)
        else:
            err(f"invalid path: {source}")
    if not sources:
        if state.verbose or not state.quiet:
            out("no python files are detected")
        ctx.exit(0)
    if doc:
        archives_doc(ctx, sources, state)
    archives_lint(ctx, sources, state)


if __name__ == "__main__":
    archives()  # noqa
