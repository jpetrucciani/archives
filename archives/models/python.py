"""
@author jacobi petrucciani
@desc python related AST classes
"""
from enum import Enum
from radon.complexity import cc_visit_ast
from radon.metrics import h_visit_ast
from typing import Dict, Set, Union
from archives.globals import ast3, DEFAULT_ARG_IGNORE
from archives.utils.text import debug
from archives.models.tags import Tags


def parse_elt(elt: Union[ast3.Name, ast3.Subscript]) -> str:
    """
    @cc 4
    @desc a function to help parse a type annotation into a string
    @arg elt: the element to attempt to parse
    @ret the string version of this type annotation
    """
    if isinstance(elt, ast3.Name):
        return elt.id
    if isinstance(elt, ast3.NameConstant):
        return elt.value
    if isinstance(elt, ast3.Subscript):
        value = elt.slice.value  # type: ignore
        name = elt.value.id  # type: ignore
        if isinstance(value, ast3.Str):
            return f"{name}[{value.s}]"
        if isinstance(value, ast3.Name):
            return f"{name}[{value.id}]"
        if isinstance(value, ast3.NameConstant):
            return f"{name}[{value.value}]"
        if isinstance(value, ast3.Tuple):
            return "{}[{}]".format(
                name, ", ".join(parse_elt(x) for x in value.elts)  # type: ignore
            )
        else:
            debug(value)
    return ""


class Annotation:
    """
    @desc representation of a type annotation in python code
    """

    def __init__(self, anno: Union[ast3.Name, ast3.Subscript]) -> None:
        """
        @cc 1
        @desc annotation constructor
        @arg anno: an AST annotation object to parse into a type
        """
        self._annotation = anno
        self.type = parse_elt(anno)

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
        """
        self._doc = doc_string
        self.value = doc_string.value.s.strip()  # type: ignore
        desc = Tags.DESC.regex.search(self.value)
        ret = Tags.RETURN.regex.search(self.value)
        cc = Tags.CC.regex.search(self.value)
        author = Tags.AUTHOR.regex.search(self.value)
        todo = Tags.TODO.regex.search(self.value)

        self.no_lint = bool(Tags.NO_LINT.regex.search(self.value))
        self.no_doc = bool(Tags.NO_DOC.regex.search(self.value))
        self.todo = todo[1] if todo else ""

        self.desc = desc[1] if desc else ""
        self.args = {
            x: y
            for x, y in Tags.ARG.regex.findall(self.value)
            if x not in DEFAULT_ARG_IGNORE
        }
        self.links = {x: y for x, y in Tags.LINK.regex.findall(self.value)}
        self.ret = ret[1] if ret else ""
        self.author = author[1] if author else ""
        self.cc = int(cc[1] if cc else -1)

        self.notes = [x for x in Tags.NOTE.regex.findall(self.value)]
        self.warnings = [x for x in Tags.WARN.regex.findall(self.value)]

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Doc[{self.desc}]>"

    def serialize(self) -> Dict:
        """
        @cc 1
        @desc serialize method for saving to json
        @ret a dict of this arg's properties
        """
        return dict(
            desc=self.desc,
            ret=self.ret,
            cc=self.cc,
            author=self.author,
            links=self.links,
            args=self.args,
            notes=self.notes,
            warnings=self.warnings,
            no_lint=self.no_lint,
        )


class Arg:
    """
    @desc representation of an arg
    """

    def __init__(self, arg: ast3.arg) -> None:
        """
        @cc 2
        @desc easier to use version of the ast arg def
        @arg arg: the AST arg object to parse
        """
        self.typed = False
        self.line = arg.lineno
        self.column = arg.col_offset
        self.name = arg.arg
        self.type = None
        self.type_line = -1
        self.type_column = -1
        if arg.annotation:
            anno = arg.annotation
            self.typed = True
            self.type = Annotation(anno)  # type: ignore
            self.type_line = anno.lineno
            self.type_column = anno.col_offset

    def __repr__(self) -> str:
        """
        @cc 1
        @desc repr dunder method
        @ret the repr representation of this Issue
        """
        return f"<Arg[{self.name}](line:{self.line})>"

    def serialize(self) -> Dict:
        """
        @cc 1
        @desc serialize method for saving to json
        @ret a dict of this arg's properties
        """
        return dict(
            name=self.name,
            typed=self.typed,
            line=self.line,
            column=self.column,
            type=str(self.type),
        )


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
        self.return_typed = False
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
            self.return_typed = True
            self.returns = parse_elt(function.returns)  # type: ignore

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

    def serialize(self) -> Dict:
        """
        @cc 1
        @desc serialize method for saving to json
        @ret a dict of this arg's properties
        """
        return dict(
            author=self.doc.author if self.doc else None,
            name=self.name,
            line=self.line,
            column=self.column,
            args=[x.serialize() for x in self.args],
            functions=[x.serialize() for x in self.functions],
            classes=[x.serialize() for x in self.classes],
            complexity=self.complexity,
            returns=self.returns,
            doc=self.doc.serialize() if self.doc else None,
        )


class Class:
    """
    @desc representation of a python class
    """

    def __init__(self, cls: ast3.ClassDef, module: "Module") -> None:
        """
        @cc 2
        @desc easier to use version of a class
        @arg cls: the AST ClassDef to parse
        @arg module: the module this class resides in
        """
        self.body = cls.body
        self.line = cls.lineno
        self.column = cls.col_offset
        self.name = cls.name
        self.module = module
        self.decorators = cls.decorator_list
        self.doc = None
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

    def serialize(self) -> Dict:
        """
        @cc 1
        @desc serialize method for saving to json
        @ret a dict of this arg's properties
        """
        return dict(
            author=self.doc.author if self.doc else None,
            name=self.name,
            line=self.line,
            column=self.column,
            functions=[x.serialize() for x in self.functions],
            classes=[x.serialize() for x in self.classes],
            doc=self.doc.serialize() if self.doc else None,
        )


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
        """
        self.doc = None
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

    def serialize(self) -> Dict:
        """
        @cc 1
        @desc serialize method for saving to json
        @ret a dict of this arg's properties
        """
        return dict(
            author=self.doc.author if self.doc else None,
            name=self.name,
            functions=[x.serialize() for x in self.functions],
            classes=[x.serialize() for x in self.classes],
            doc=self.doc.serialize() if self.doc else None,
        )
