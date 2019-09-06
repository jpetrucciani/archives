"""
archives
- perhaps the archives are incomplete?
"""
import click
import os
import re
from collections import defaultdict
from enum import Enum
from functools import lru_cache, partial
from pathlib import Path
from typed_ast import ast3
from typing import Callable, Iterator, Iterable, List, Pattern, Set, Tuple, Union


__version__ = "0.1"
DEFAULT_EXCLUDES_LIST = [
    r"\.eggs",
    r"\.git",
    r"\.hg",
    r"\.mypy_cache",
    r"\.nox",
    r"\.tox",
    r"\.venv",
    r"env",
    r"_build",
    r"buck-out",
    r"build",
    r"dist",
]
DEFAULT_EXCLUDES = r"/(" + "|".join(DEFAULT_EXCLUDES_LIST) + ")/"
DEFAULT_INCLUDES = r"\.pyi?$"

OUT = partial(click.secho, bold=True, err=True)
ERR = partial(click.secho, fg="red", err=True)
MSG = partial(click.secho, fg="blue", err=True)


# templates for archives tags
CHAR = "@"
EOL = r"(?:\n|\Z)"
DESC = re.compile(rf"(?:{CHAR}desc) (.+){EOL}")
ARG = re.compile(rf"(?:{CHAR}arg) ([a-zA-Z0-9_]+) (.+){EOL}")
RETURN = re.compile(rf"(?:{CHAR}ret) (.+){EOL}")
LINK = re.compile(rf"(?:{CHAR}link) ([a-zA-Z0-9_]+) (.+){EOL}")


DEFAULT_ARG_IGNORE = ["self", "cls"]

FORMATS = {
    "flake8": "{path}:{line}:{column}: {code} {text} for '{name}'",
    "pylint": "{path}:{line}: [{code}] {text} for '{name}'",
}


class Rule:
    """a rule for an issue with the archives"""

    def __init__(self, code: str, desc: str, check: Callable) -> None:
        """issue constructor"""
        self.code = code
        self.check = check
        self.desc = desc


class Issue:
    """an instance of an Rule being flagged"""

    def __init__(self, rule: Rule, obj: Union["Class", "Function", "Module"]) -> None:
        """constructor for issue"""
        self.rule = rule
        self.obj = obj
        self.line = 0 if isinstance(obj, Module) else obj.line
        self.column = 0 if isinstance(obj, Module) else obj.column

    def __str__(self) -> str:
        """string representation of this issue"""
        return f"<Issue[{self.rule.code}] {self.obj}>"

    def __repr__(self) -> str:
        """repl repr for an issue"""
        return self.__str__()


def no_docstring(obj: Union["Class", "Function", "Module"]) -> bool:
    """returns true if the obj has no docstring"""
    return not obj.doc


def no_desc(obj: Union["Class", "Function", "Module"]) -> bool:
    """returns true if the obj has no @desc tag"""
    return not obj.doc or not obj.doc.desc


MODULE_RULES = [
    Rule("M100", "module missing a docstring", no_docstring),
    Rule("M101", "module missing an @desc tag", no_desc),
]
CLASS_RULES = [
    Rule("C100", "class missing a docstring", no_docstring),
    Rule("C101", "class missing an @desc tag", no_desc),
]
FUNCTION_RULES = [
    Rule("F100", "function missing a docstring", no_docstring),
    Rule("F101", "function missing an @desc tag", no_desc),
]


class Doc:
    """representation of a doc string"""

    class Type(Enum):
        """what type of docstring?"""

        FUNCTION = 0
        CLASS = 1
        MODULE = 2

    def __init__(self, doc_string: ast3.Expr, doc_type: Type) -> None:
        """easier to use version of the ast docstring def"""
        self.value = doc_string.value.s.strip()  # type: ignore
        desc = DESC.search(self.value)
        ret = RETURN.search(self.value)

        self.desc = desc[1] if desc else ""
        self.args = {
            x: y for x, y in ARG.findall(self.value) if x not in DEFAULT_ARG_IGNORE
        }
        self.links = {
            x: y for x, y in LINK.findall(self.value) if x not in DEFAULT_ARG_IGNORE
        }
        self.ret = ret[1] if ret else ""

    def __repr__(self) -> str:
        """repr for doc"""
        return f"<Doc>"


class Arg:
    """representation of an arg"""

    def __init__(self, arg: ast3.arg) -> None:
        """easier to use version of the ast arg def"""
        self.typed = False
        self.line = arg.lineno
        self.column = arg.col_offset
        self.name = arg.arg
        if arg.annotation:
            self.typed = True
            self.type = arg.annotation.id  # type: ignore
            self.type_line = arg.annotation.lineno
            self.type_column = arg.annotation.col_offset

    def __repr__(self) -> str:
        """repr for arg"""
        return f"<Arg[{self.name}](line:{self.line})>"


class Function:
    """representation of a function"""

    def __init__(self, function: ast3.FunctionDef, module: "Module") -> None:
        """easier to use version of the ast function def"""
        self.name = function.name
        self.line = function.lineno
        self.column = function.col_offset
        self.body = function.body
        self.module = module
        self.decorators = function.decorator_list
        self._args = function.args.args
        self.args = [Arg(x) for x in self._args]
        self.functions = [
            Function(x, self.module)
            for x in self.body
            if isinstance(x, ast3.FunctionDef)
        ]
        self.classes = [
            Class(x, self.module) for x in self.body if isinstance(x, ast3.ClassDef)
        ]
        self.untyped = [
            x for x in self.args if not x.typed and x not in DEFAULT_ARG_IGNORE
        ]
        self.doc = None
        self.missing_args: Set[str] = set()
        self.unexpected_args: Set[str] = set()
        arg_names = set(x.name for x in self.args if x.name not in DEFAULT_ARG_IGNORE)
        if isinstance(self.body[0], ast3.Expr):
            # this is most likely a doc string
            self.doc = Doc(self.body[0], Doc.Type.FUNCTION)
            doc_arg_names = set(x for x, y in self.doc.args.items())
            self.missing_args = arg_names - doc_arg_names
            self.unexpected_args = doc_arg_names - arg_names

    def __repr__(self) -> str:
        """repr for function"""
        return f"<Function[{self.name}](line:{self.line})>"


class Class:
    """representation of a python class"""

    def __init__(self, cls: ast3.ClassDef, module: "Module") -> None:
        """easier to use version of a cls"""
        self.body = cls.body
        self.line = cls.lineno
        self.column = cls.col_offset
        self.name = cls.name
        self.module = module
        self.decorators = cls.decorator_list
        self.functions = [
            Function(x, self.module)
            for x in self.body
            if isinstance(x, ast3.FunctionDef)
        ]
        self.classes = [
            Class(x, self.module) for x in self.body if isinstance(x, ast3.ClassDef)
        ]
        if isinstance(self.body[0], ast3.Expr):
            # this is most likely a doc string
            self.doc = Doc(self.body[0], Doc.Type.CLASS)

    def __repr__(self) -> str:
        """repr for module"""
        return f"<Class[{self.name}](line:{self.line})>"


class Module:
    """representation of a python module"""

    def __init__(self, module: ast3.Module, filename: str) -> None:
        """easier to use version of a module"""
        self.body = module.body
        self.path = filename
        self.name = self.path.split("/")[-1]
        self.functions = [
            Function(x, self) for x in self.body if isinstance(x, ast3.FunctionDef)
        ]
        self.classes = [
            Class(x, self) for x in self.body if isinstance(x, ast3.ClassDef)
        ]
        if isinstance(self.body[0], ast3.Expr):
            # this is most likely a doc string
            self.doc = Doc(self.body[0], Doc.Type.MODULE)

    def __repr__(self) -> str:
        """repr for module"""
        return f"<Module[{self.path}]>"


def parse_module(filename: str) -> Module:
    """parse a module into our archives models"""
    if not os.path.isfile(filename):
        raise Exception("file does not exist")
    contents = ""
    with open(filename, encoding="utf-8", errors="replace") as file_to_read:
        contents += file_to_read.read()
    return Module(ast3.parse(contents), filename)  # type: ignore


def get_python_files(
    path: Path, root: Path, include: Pattern[str], exclude: Pattern[str]
) -> Iterator[Path]:
    """
    Generate all files under `path` whose paths are not excluded by the
    `exclude` regex, but are included by the `include` regex.
    Symbolic links pointing outside of the `root` directory are ignored.
    `report` is where output about exclusions goes.
    """
    assert root.is_absolute(), f"INTERNAL ERROR: `root` must be absolute but is {root}"
    for child in path.iterdir():
        try:
            normalized_path = "/" + child.resolve().relative_to(root).as_posix()
        except ValueError:
            if child.is_symlink():
                continue

            raise

        if child.is_dir():
            normalized_path += "/"
        exclude_match = exclude.search(normalized_path)
        if exclude_match and exclude_match.group(0):
            continue

        if child.is_dir():
            yield from get_python_files(child, root, include, exclude)

        elif child.is_file():
            include_match = include.search(normalized_path)
            if include_match:
                yield child


@lru_cache()
def find_project_root(srcs: Iterable[str]) -> Path:
    """
    Return a directory containing .git, .hg, or pyproject.toml.
    That directory can be one of the directories passed in `srcs` or their
    common parent.
    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.
    """
    if not srcs:
        return Path("/").resolve()

    common_base = min(Path(src).resolve() for src in srcs)
    if common_base.is_dir():
        # Append a fake file so `parents` below returns `common_base_dir`, too.
        common_base /= "fake-file"
    for directory in common_base.parents:
        if (directory / ".git").is_dir():
            return directory

    return directory


def function_lint(
    function: Function,
    class_rules: List[Rule] = None,
    function_rules: List[Rule] = None,
) -> List:
    """function specific lint"""
    if not class_rules:
        class_rules = CLASS_RULES
    if not function_rules:
        function_rules = FUNCTION_RULES

    issues = []

    # check this function for rules
    for rule in function_rules:
        if rule.check(function):
            issues.append(Issue(rule, function))

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
    """class specific lint"""
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
    """lint the given module, returning an exit code if any errors"""
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
    src: Tuple[str],
) -> None:
    """archives"""
    try:
        include_regex = re.compile(include)
    except re.error:
        ERR(f"invalid regex for include: {include!r}")
        ctx.exit(2)
    try:
        exclude_regex = re.compile(exclude)
    except re.error:
        ERR(f"invalid regex for exclude: {exclude!r}")
        ctx.exit(2)
    root = find_project_root(src)
    sources: Set[Path] = set()
    path_empty(src, quiet, verbose, ctx)
    for source in src:
        path = Path(source)
        if path.is_dir():
            sources.update(get_python_files(path, root, include_regex, exclude_regex))
        elif path.is_file() or source == "-":
            # if a file was explicitly given, we don't care about its extension
            sources.add(path)
        else:
            ERR(f"invalid path: {source}")
    if not sources:
        if verbose or not quiet:
            OUT("no python files are detected")
        ctx.exit(0)

    # apply disables
    disable_list = disable.split(",")
    module_rules = [x for x in MODULE_RULES if x.code not in disable_list]
    class_rules = [x for x in CLASS_RULES if x.code not in disable_list]
    function_rules = [x for x in FUNCTION_RULES if x.code not in disable_list]

    # do stuff with the files
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
        message = FORMATS[format].format_map(
            defaultdict(
                str,
                path=module.path,
                line=issue.line,
                column=issue.column,
                code=rule.code,
                text=rule.desc,
                name=obj.name,
            )
        )
        MSG(message)

    ctx.exit(0 if not issues else 1)


def path_empty(src: Tuple[str], quiet: bool, verbose: bool, ctx: click.Context) -> None:
    """Exit if there is no src provided for formatting"""
    if not src:
        if verbose or not quiet:
            OUT("no path provided")
            ctx.exit(0)


if __name__ == "__main__":
    archives()  # noqa
