"""
@author jacobi petrucciani
@desc perhaps the archives are incomplete?
"""
import click
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Set, Tuple
from archives.globals import (
    ast3,
    DEFAULT_INCLUDES,
    DEFAULT_EXCLUDES,
    DEFAULT_ARG_IGNORE,
    FORMATS,
    __version__,
)
from archives.models.python import Class, Function, Module
from archives.models.rules import Issue
from archives.models.tags import Tags, CHAR
from archives.utils.state import get_state, State
from archives.utils.files import (
    find_project_root,
    path_empty,
    get_python_files,
    decode_bytes,
)
from archives.utils.text import out, err
from archives.rules import (
    MODULE_RULES,
    CLASS_RULES,
    FUNCTION_RULES,
    MISSING_ARG,
    UNEXPECTED_ARG,
    UNTYPED_ARG,
)


def parse_module(filename: str) -> Module:
    """
    @cc 3
    @desc parse a module into our archives' models
    @arg filename: the python file to parse
    @ret a parsed Module object of the given file
    """
    state = get_state()
    contents = ""
    if str(filename)[-2:] == "/-":
        contents, _, __ = decode_bytes(sys.stdin.buffer.read())
    elif not os.path.isfile(filename):
        raise Exception("file does not exist")
    else:
        with open(filename, encoding="utf-8", errors="replace") as file_to_read:
            contents += file_to_read.read()
    try:
        ast = ast3.parse(contents)
    except:  # noqa
        out("error in parsing", color="red")
        if state.ignore_exceptions:
            sys.exit(0)
    module = Module(ast, filename)  # type: ignore
    return module


def function_lint(function: Function) -> List:
    """
    @cc 8
    @desc function specific lint
    @arg function: the Function object to lint
    @ret a list of issues found in this function
    """
    state = get_state()
    issues = []

    state.function_count += 1

    if function.doc and function.doc.no_lint:
        state.function_nolint_count += 1
        return []

    # check this function for rules
    for rule in state.function_rules:
        if rule.check(function):
            issues.append(Issue(rule, function))

    # check for missing args
    if MISSING_ARG.code not in state.disable_list:
        for arg_name in function.missing_args:
            issues.append(Issue(MISSING_ARG, function, dict(arg=arg_name)))

    # check for unexpected args
    if UNEXPECTED_ARG.code not in state.disable_list:
        for arg_name in function.unexpected_args:
            issues.append(Issue(UNEXPECTED_ARG, function, dict(arg=arg_name)))

    # check for untyped args
    if UNTYPED_ARG.code not in state.disable_list:
        for arg in [
            x for x in function.args if not x.typed and x.name not in DEFAULT_ARG_IGNORE
        ]:
            issues.append(Issue(UNTYPED_ARG, function, dict(arg=arg)))

    # check nested classes
    for sub_class in function.classes:
        issues.extend(class_lint(sub_class))

    # check all sub functions
    for sub_function in function.functions:
        issues.extend(function_lint(sub_function))

    return issues


def class_lint(class_def: Class) -> List:
    """
    @cc 5
    @desc class specific lint
    @arg class_def: the Class object to lint
    @ret a list of issues found in this class
    """

    state = get_state()
    issues = []

    state.class_count += 1

    if class_def.doc and class_def.doc.no_lint:
        state.class_nolint_count += 1
        return []

    # check this class for rules
    for rule in state.class_rules:
        if rule.check(class_def):
            issues.append(Issue(rule, class_def))

    # check nested classes
    for sub_class in class_def.classes:
        issues.extend(class_lint(sub_class))

    # check functions within this class
    for function in class_def.functions:
        issues.extend(function_lint(function))

    return issues


def lint(module: Module) -> List:
    """
    @cc 5
    @desc lint the given module!
    @arg module: the module to lint
    @ret a list of issues found in this module
    """

    issues = []
    state = get_state()

    state.module_count += 1

    if module.doc and module.doc.no_lint:
        state.module_nolint_count += 1
        return []

    for rule in state.module_rules:
        if rule.check(module):
            issues.append(Issue(rule, module))

    for class_def in module.classes:
        issues.extend(class_lint(class_def))

    for function in module.functions:
        issues.extend(function_lint(function))

    return issues


def archives_lint(ctx: click.Context, sources: Set[Path], state: State) -> None:
    """
    @cc 4
    @desc perform an archives documentation lint
    @arg ctx: the click context of the current run
    @arg sources: the source files to lint
    @arg state: the current click state
    """

    # apply disables to the global rule state
    state.module_rules = [x for x in MODULE_RULES if x.code not in state.disable_list]
    state.class_rules = [x for x in CLASS_RULES if x.code not in state.disable_list]
    state.function_rules = [
        x for x in FUNCTION_RULES if x.code not in state.disable_list
    ]

    # lint the files
    issues = []
    for file in sources:
        module = parse_module(str(file.absolute()))
        issues.extend(lint(module))

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
        out(message, color="blue")
    if not state.quiet:
        if issues:
            trailing_s = "s" if len(issues) != 1 else ""
            out(f"\nImpossible! Perhaps your archives are incomplete?", color="red")
            out(f"{len(issues)} issue{trailing_s} found", color="red")
        else:
            out(
                f"Incredible! It appears that your archives are complete!", color="blue"
            )
            out(f"0 issues found", color="blue")

        if state.stats:
            _mods = state.module_count
            _cls = state.class_count
            _fns = state.function_count
            out(
                f"{_mods} module{'s' if _mods != 1 else ''} ({state.module_nolint_count} nolint)"
            )
            out(
                f"{_cls} class{'es' if _cls != 1 else ''} ({state.class_nolint_count} nolint)"
            )
            out(
                f"{_fns} function{'s' if _fns != 1 else ''} ({state.function_nolint_count} nolint)"
            )

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
    "--list-tags",
    is_flag=True,
    default=False,
    is_eager=True,
    help="list all active tags",
)
@click.option(
    "--doc",
    is_flag=True,
    default=False,
    help="generate documentation for the given sources",
)
@click.option(
    "--ignore-exceptions",
    is_flag=True,
    default=False,
    help="ignore parsing exceptions (useful for ci)",
)
@click.option(
    "--stats",
    is_flag=True,
    default=False,
    help="print out additional stats for this linting run",
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
    list_tags: bool,
    stats: bool,
    ignore_exceptions: bool,
    doc: bool,
    src: Tuple[str],
) -> None:
    """
    check if your code's archives are incomplete!
    \f
    @cc 8
    @desc the main cli method for archives
    @arg ctx: the click context arg
    @arg quiet: the cli quiet flag
    @arg verbose: the cli verbose flag
    @arg include: a regex for what files to include
    @arg exclude: a regex for what files to exclude
    @arg format: a flag to specify output format for the issues
    @arg disable: a comma separated disable list for rules
    @arg list_rules: a flag to print the list of rules and exit
    @arg list_tags: a flag to print the list of tags and their descriptions
    @arg stats: a flag to print extra stats at the end of a lint run
    @arg ignore_exceptions: a flag to ignore parsing errors and exit 0
    @arg doc: a flag to specify if we should generate docs instead of lint
    @arg src: a file or directory to scan for files to lint
    """
    state = ctx.ensure_object(State)
    state.verbose = verbose
    state.quiet = quiet
    state.format = format
    state.disable_list = disable.split(",")
    state.ignore_exceptions = ignore_exceptions
    state.stats = stats

    if list_rules:
        for rule in [
            *MODULE_RULES,
            *CLASS_RULES,
            *FUNCTION_RULES,
            MISSING_ARG,
            UNEXPECTED_ARG,
            UNTYPED_ARG,
        ]:
            out(f"{rule.code}: {rule.desc}")
        ctx.exit(0)
    if list_tags:
        for tag in Tags.all():
            out(f"{CHAR}{tag.name}\t{tag.desc}")
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
