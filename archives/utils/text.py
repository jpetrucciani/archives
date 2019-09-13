"""
@author jacobi petrucciani
@desc text related helpers for archives
"""
import click
import json
from typing import Dict, List, Union
from archives.utils.state import get_state


def debug(data: Union[str, Dict, List], force: bool = False) -> None:
    """
    @cc 2
    @desc only prints if verbose mode is on, formatting nicely if list/dict
    @arg data: either a string to print, or a list/dict to print nicely
    @arg force: force this debug to print, regardless of state/flags
    """
    state = get_state()
    if state.verbose or force:
        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2, sort_keys=True, default=str)
        click.echo(click.style(data, fg="green"), err=True)


def out(
    data: Union[str, Dict, List], force: bool = False, color: str = "green"
) -> None:
    """
    @cc 2
    @desc prints something to standard out
    @arg data: either a string to print, or a list/dict to print nicely
    @arg color: what color to print in
    @arg force: force this debug to print, regardless of state/flags
    """
    state = get_state()
    if not state.quiet or force:
        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2, sort_keys=True, default=str)
        click.echo(click.style(data, fg=color))


def err(data: Union[str, Dict, List]) -> None:
    """
    @cc 2
    @desc prints something to standard error
    @arg data: either a string to print, or a list/dict to print nicely
    """
    state = get_state()
    if not state.quiet:
        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2, sort_keys=True, default=str)
        click.secho(data, fg="red", err=True)


def msg(data: Union[str, Dict, List]) -> None:
    """
    @cc 2
    @desc prints something to standard out in blue
    @arg data: either a string to print, or a list/dict to print nicely
    """
    state = get_state()
    if not state.quiet:
        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2, sort_keys=True, default=str)
        click.secho(data, fg="blue")
