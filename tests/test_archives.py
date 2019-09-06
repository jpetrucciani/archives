"""
tests for archives
"""
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
    assert result.exit_code == 0
    assert "no path provided" in result.output


def test_help():
    """test that no files are passed in"""
    result = run(archives, ["--help"])
    assert result.exit_code == 0
    assert "check if your code's archives are incomplete!" in result.output
