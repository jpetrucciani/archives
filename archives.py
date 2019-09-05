"""
archives
- perhaps the archives are incomplete?
"""
import click
import os
import re
from enum import Enum
from functools import lru_cache, partial
from pathlib import Path
from typed_ast import ast3
from typing import Iterator, Iterable, Pattern, Set, Tuple, Union


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


CHAR = "@"
EOL = r"(?:\n|\Z)"
DESC = re.compile(rf"(?:{CHAR}desc) (.+){EOL}")
ARG = re.compile(rf"(?:{CHAR}arg) ([a-zA-Z0-9_]+) (.+){EOL}")
RETURN = re.compile(rf"(?:{CHAR}ret) (.+){EOL}")
LINK = re.compile(rf"(?:{CHAR}link) ([a-zA-Z0-9_]+) (.+){EOL}")

DEFAULT_ARG_IGNORE = ["self", "cls"]


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

    def __init__(self, function: ast3.FunctionDef) -> None:
        """easier to use version of the ast function def"""
        self.name = function.name
        self.line = function.lineno
        self.column = function.col_offset
        self.body = function.body
        self.decorators = function.decorator_list
        self._args = function.args.args
        self.args = [Arg(x) for x in self._args]
        self.functions = [
            Function(x) for x in self.body if isinstance(x, ast3.FunctionDef)
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

    def __init__(self, cls: ast3.ClassDef) -> None:
        """easier to use version of a cls"""
        self.body = cls.body
        self.line = cls.lineno
        self.column = cls.col_offset
        self.name = cls.name
        self.decorators = cls.decorator_list
        self.functions = [
            Function(x) for x in self.body if isinstance(x, ast3.FunctionDef)
        ]
        self.classes = [Class(x) for x in self.body if isinstance(x, ast3.ClassDef)]
        if isinstance(self.body[0], ast3.Expr):
            # this is most likely a doc string
            self.doc = Doc(self.body[0], Doc.Type.CLASS)

    def __repr__(self) -> str:
        """repr for module"""
        return f"<Class[{self.name}](line:{self.line})>"


class Module:
    """representation of a python module"""

    def __init__(self, module: ast3.Module, name: str) -> None:
        """easier to use version of a module"""
        self.body = module.body
        self.name = name
        self.functions = [
            Function(x) for x in self.body if isinstance(x, ast3.FunctionDef)
        ]
        self.classes = [Class(x) for x in self.body if isinstance(x, ast3.ClassDef)]
        if isinstance(self.body[0], ast3.Expr):
            # this is most likely a doc string
            self.doc = Doc(self.body[0], Doc.Type.MODULE)

    def __repr__(self) -> str:
        """repr for module"""
        return f"<Module[{self.name}]>"


def parse_module(filename: str) -> Module:
    """parse a module into our archives models"""
    if not os.path.isfile(filename):
        raise Exception("file does not exist")
    contents = ""
    with open(filename, encoding="utf-8", errors="replace") as file_to_read:
        contents += file_to_read.read()
    return Module(ast3.parse(contents), filename.split("/")[-1])  # type: ignore


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


def function_lint(function: Function, parent: Union[Module, Class, Function]) -> int:
    """function specific lint"""
    if function.unexpected_args or function.missing_args:
        for arg in function.unexpected_args:
            ERR(f"{parent.name}[{function.name}] unexpected arg {arg}")
        for arg in function.missing_args:
            ERR(f"{parent.name}[{function.name}] missing arg {arg}")
        return 1
    return 0


def lint(module: Module) -> int:
    """lint the given module, returning an exit code if any errors"""
    return_code = 0
    ERR(f"linting {module.name}: {module.functions}")
    for function in module.functions:
        ERR(f"\tlinting {function.name}")
        if function_lint(function, module) != 0:
            return_code = 1

    for class_def in module.classes:
        for function in class_def.functions:
            if function_lint(function, class_def) != 0:
                return_code = 1
    return return_code


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--include", type=str, default=DEFAULT_INCLUDES, show_default=True)
@click.option("--exclude", type=str, default=DEFAULT_EXCLUDES, show_default=True)
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
    src: Tuple[str],
) -> None:
    """archives"""
    return_code = 0
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

    # do stuff with the files
    for file in sources:
        module = parse_module(str(file))
        response = lint(module)
        if response != 0:
            return_code = 1

    ctx.exit(return_code)


def path_empty(src: Tuple[str], quiet: bool, verbose: bool, ctx: click.Context) -> None:
    """Exit if there is no src provided for formatting"""
    if not src:
        if verbose or not quiet:
            OUT("no path provided")
            ctx.exit(0)


if __name__ == "__main__":
    archives()  # noqa
