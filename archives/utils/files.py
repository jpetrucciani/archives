"""
@author jacobi petrucciani
@desc file related helper utils
"""
import click
import io
import tokenize
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Iterable, Pattern, Tuple
from archives.utils.text import err
from archives.utils.state import get_state


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


def path_empty(src: Tuple[str], ctx: click.Context) -> None:
    """
    @cc 2
    @desc Exit if there is no src provided for formatting
    @arg src: a list of source files to lint
    @arg ctx: the context of the click cli application
    """
    state = get_state()
    if not src:
        if state.verbose or not state.quiet:
            err("no paths provided!")
        ctx.exit(2)


def decode_bytes(src: bytes) -> Tuple[str, str, str]:
    """
    @cc 2
    @desc decode bytes passed in
    @arg src: source data
    @ret a tuple of (decoded_contents, encoding, newline)
    """
    srcbuf = io.BytesIO(src)
    encoding, lines = tokenize.detect_encoding(srcbuf.readline)
    if not lines:
        return "", encoding, "\n"

    newline = "\r\n" if b"\r\n" == lines[0][-2:] else "\n"
    srcbuf.seek(0)
    with io.TextIOWrapper(srcbuf, encoding) as tiow:
        return tiow.read(), encoding, newline
