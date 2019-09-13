"""
tests for archives
"""
import json
from click.testing import CliRunner
from archives import archives
from typing import Callable, List


def run(function: Callable, args: List = None):
    """helper to run archives commands"""
    runner = CliRunner()
    return runner.invoke(function, args)  # type: ignore


def test_no_files():
    """test that no files are passed in"""
    result = run(archives)
    assert result.exit_code == 2
    assert "no paths provided!" in result.output


def test_help():
    """test the help flag"""
    result = run(archives, ["--help"])
    assert result.exit_code == 0
    assert "check if your code's archives are incomplete!" in result.output


def test_list_rules():
    """test listing rules flag"""
    result = run(archives, ["--list-rules"])
    assert result.exit_code == 0
    assert "F101" in result.output


def test_doc_gen():
    """test doc flag"""
    result = run(archives, ["--doc", "./extra/test.py"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data
    assert data["test.py"]["functions"][0]["returns"] == "Union[int, float, str]"


def test_no_lint():
    """test doc flag"""
    result = run(archives, ["./extra/no_lint.py"])
    assert result.exit_code == 1
    assert "Impossible! Perhaps your archives are incomplete?" in result.output
    assert "1 issue found" in result.output


def test_archives_self():
    """test running archives on itself!"""
    result = run(archives, ["./archives/"])
    assert result.exit_code == 0
    assert "0 issues found" in result.output
