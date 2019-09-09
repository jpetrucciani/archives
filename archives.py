"""
archives
@desc perhaps the archives are incomplete?
"""
import click
import os
import re
from collections import defaultdict
from enum import Enum
from functools import lru_cache, partial
from pathlib import Path
from radon.complexity import cc_visit_ast
from radon.metrics import h_visit_ast
from typed_ast import ast3
from typing import Callable, Dict, Iterator, Iterable, List, Pattern, Set, Tuple, Union


__version__ = "0.4"
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
class Tag:
    """
    @desc tag namespace
    """

    CHAR = "@"
    EOL = r"(?:\n|\Z)"
    CC = re.compile(rf"(?:{CHAR}cc) ([0-9]+){EOL}")
    DESC = re.compile(rf"(?:{CHAR}desc):? (.+){EOL}")
    ARG = re.compile(rf"(?:{CHAR}arg) ([a-zA-Z0-9_]+):? (.+){EOL}")
    RETURN = re.compile(rf"(?:{CHAR}ret):? (.+){EOL}")
    LINK = re.compile(rf"(?:{CHAR}link) ([a-zA-Z0-9_]+):? (.+){EOL}")


DEFAULT_ARG_IGNORE = ["self", "cls"]

FORMATS = {
    "flake8": "{path}:{line}:{column}: {code} {text}",
    "pylint": "{path}:{line}: [{code}] {text}",
}


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
        @ret nothing
        """
        self.code = code
        self.check = check
        self.desc = desc


class Issue:
    """
    @desc an instance of a Rule being flagged
    """

    def __init__(
        self, rule: Rule, obj: Union["Class", "Function", "Module"], extra: Dict = None
    ) -> None:
        """
        @cc 1
        @desc constructor for issue
        @arg rule: an instance of the rule being broken
        @arg obj: either a class, function, or module that breaks the rule
        @arg extra: extra data to pass to the issue description template
        @ret nothing
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


def no_docstring(obj: Union["Class", "Function", "Module"]) -> bool:
    """
    @cc 1
    @desc no docstring test
    @arg obj: a class, function, or module to check
    @ret true if the obj has no docstring
    """
    return not obj.doc


def no_desc(obj: Union["Class", "Function", "Module"]) -> bool:
    """
    @cc 1
    @desc no description test
    @arg obj: a class, function, or module to check
    @ret true if the obj has no @desc tag
    """
    return not obj.doc or not obj.doc.desc


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


def no_ret(obj: "Function") -> bool:
    """
    @cc 1
    @desc no return tag test
    @arg obj: a function to check
    @ret true if the function does not have a @ret tag
    """
    return not obj.doc or not obj.doc.ret


def nop(obj: Union["Class", "Function", "Module"]) -> bool:
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
]
MISSING_ARG = Rule("F105", "function '{name}' missing @arg for '{arg}'", nop)
UNEXPECTED_ARG = Rule("F106", "function '{name}' unexpected @arg for '{arg}'", nop)


class Annotation:
    """
    @desc representation of a type annotation in python code
    """

    def __init__(self, anno) -> None:
        """
        @cc 3
        @desc annotation constructor
        @arg anno: an AST annotation object to parse
        @ret nothing
        """
        self.type = ""
        self._annotation = anno
        if isinstance(anno, ast3.Name):
            self.type = anno.id
        if isinstance(anno, ast3.Subscript):
            value = anno.slice.value  # type: ignore
            if isinstance(value, ast3.Name):
                internal = value.id
            else:
                internal = ", ".join([x.s for x in value.elts])
            self.type = f"{anno.value.id}[{internal}]"  # type: ignore

    def __str__(self) -> str:
        """
        @cc 1
        @desc string dunder method
        @ret the string representation of this Annotation
        """
        return self.type

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repl representation of this Annotation
        """
        return self.__str__()


class Doc:
    """
    @desc representation of a doc string
    """

    class Type(Enum):
        """
        @desc enum for the type of docstring
        """

        FUNCTION = 0
        CLASS = 1
        MODULE = 2

    def __init__(self, doc_string: ast3.Expr, doc_type: Type) -> None:
        """
        @cc 1
        @desc easier to use version of the ast docstring def
        @arg doc_string: the expression used to represent a docstring
        @arg doc_type: the enum type of doc string this is used for
        @ret nothing
        """
        self.value = doc_string.value.s.strip()  # type: ignore
        desc = Tag.DESC.search(self.value)
        ret = Tag.RETURN.search(self.value)
        cc = Tag.CC.search(self.value)

        self.desc = desc[1] if desc else ""
        self.args = {
            x: y for x, y in Tag.ARG.findall(self.value) if x not in DEFAULT_ARG_IGNORE
        }
        self.links = {
            x: y for x, y in Tag.LINK.findall(self.value) if x not in DEFAULT_ARG_IGNORE
        }
        self.ret = ret[1] if ret else ""
        self.cc = int(cc[1] if cc else -1)

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Doc>"


class Arg:
    """
    @desc representation of an arg
    """

    def __init__(self, arg: ast3.arg) -> None:
        """
        @cc 2
        @desc easier to use version of the ast arg def
        @arg arg: the AST arg object to parse
        @ret nothing
        """
        self.typed = False
        self.line = arg.lineno
        self.column = arg.col_offset
        self.name = arg.arg
        if arg.annotation:
            anno = arg.annotation
            self.typed = True
            self.type = Annotation(anno)
            self.type_line = anno.lineno
            self.type_column = anno.col_offset

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Arg[{self.name}](line:{self.line})>"


class Function:
    """
    @desc representation of a function
    """

    def __init__(self, function: ast3.FunctionDef, module: "Module") -> None:
        """
        @cc 3
        @desc easier to use version of the ast function def
        @arg function: the AST functionDef to parse
        @arg module: the module this function resides in
        @ret nothing
        """

        # easy data
        self._function = function
        self.name = function.name
        self.line = function.lineno
        self.column = function.col_offset
        self.body = function.body
        self.module = module
        self.decorators = function.decorator_list

        # time to parse arguments
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
        self.returns = None
        self.missing_args: Set[str] = set()
        self.unexpected_args: Set[str] = set()
        arg_names = set(x.name for x in self.args if x.name not in DEFAULT_ARG_IGNORE)
        self.missing_args = arg_names
        if isinstance(self.body[0], ast3.Expr):
            # this is most likely a doc string
            self.doc = Doc(self.body[0], Doc.Type.FUNCTION)
            doc_arg_names = set(x for x, y in self.doc.args.items())
            self.missing_args = arg_names - doc_arg_names
            self.unexpected_args = doc_arg_names - arg_names
        if function.returns:
            ret = function.returns
            try:
                self.returns = ret  # type: ignore
            except AttributeError:
                self.type = ret.value  # type: ignore

        # complexity checks
        self._radon = cc_visit_ast(self._function)[0]
        self.complexity = self._radon.complexity
        self.is_method = self._radon.is_method
        self._halstead = h_visit_ast(self._function)

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Function[{self.name}](line:{self.line})>"


class Class:
    """
    @desc representation of a python class
    """

    def __init__(self, cls: ast3.ClassDef, module: "Module") -> None:
        """
        @cc 2
        @desc easier to use version of a class
        @arg cls: the AST classDef to parse
        @arg module: the module this class resides in
        @ret nothing
        """
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
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Class[{self.name}](line:{self.line})>"


class Module:
    """
    @desc representation of a python module
    """

    def __init__(self, module: ast3.Module, filename: str) -> None:
        """
        @cc 2
        @desc easier to use version of a module
        @arg module: the AST module to parse
        @arg filename: the filename of the module we're parsing
        @ret nothing
        """
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
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Module[{self.path}]>"


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


def get_python_files(
    path: Path, root: Path, include: Pattern[str], exclude: Pattern[str]
) -> Iterator[Path]:
    """
    @cc 3
    @desc return the list of files in the path, including/excluding from args
    @arg path: the path to start with
    @arg root: the root of the overall path
    @arg include: a regex for including files
    @arg exclude: a regex for excluding files
    @ret an iterator of all files found in this path
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
def find_project_root(sources: Iterable[str]) -> Path:
    """
    @cc 4
    @desc find the project root of the sources supplied
    @arg sources: a list of source files that we're parsing
    @ret the path pointing to the root of the python project
    """
    if not sources:
        return Path("/").resolve()

    common_base = min(Path(src).resolve() for src in sources)
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
    """
    @cc 8
    @desc function specific lint
    @arg function: the Function object to lint
    @arg class_rules: the altered list of class rules to check
    @arg function_rules: the altered list of function rules to check
    @ret a list of issues found in this function
    """
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
    for arg in function.missing_args:
        issues.append(Issue(MISSING_ARG, function, dict(arg=arg)))

    # check for unexpected args
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
    src: Tuple[str],
) -> None:
    """
    check if your code's archives are incomplete!
    \f
    @cc 9
    @desc the main cli method for archives
    @arg ctx: the click context arg
    @arg quiet: the cli quiet flag
    @arg verbose: the cli verbose flag
    @arg include: a regex for what files to include
    @arg exclude: a regex for what files to exclude
    @arg format: a flag to specify output format for the issues
    @arg disable: a comma separated disable list for rules
    @arg list_rules: a flag to print the list of rules and exit
    @arg src: a file or directory to scan for files to lint
    @ret nothing
    """
    if list_rules:
        for rule in [
            *MODULE_RULES,
            *CLASS_RULES,
            *FUNCTION_RULES,
            MISSING_ARG,
            UNEXPECTED_ARG,
        ]:
            OUT(f"{rule.code}: {rule.desc}")
        ctx.exit(0)
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

        message = FORMATS[format].format_map(
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
        MSG(message)

    if verbose:
        if issues:
            ERR(
                f"\nImpossible! Perhaps your archives are incomplete?\n{len(issues)} issues found."
            )
        else:
            MSG(f"Incredible! It appears that your archives are complete!")

    ctx.exit(0 if not issues else 1)


def path_empty(src: Tuple[str], quiet: bool, verbose: bool, ctx: click.Context) -> None:
    """
    @cc 2
    @desc Exit if there is no src provided for formatting
    @arg src: a list of source files to lint
    @arg quiet: if quiet mode is turned on
    @arg verbose: if verbose mode is on
    @arg ctx: the context of the click cli application
    """
    if not src:
        if verbose or not quiet:
            OUT("no paths provided!")
        ctx.exit(2)


if __name__ == "__main__":
    archives()  # noqa
