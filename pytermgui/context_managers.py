"""
pytermgui.context_managers
--------------------------
author: bczsalba


Module providing context-manager classes & functions.
"""

from os import name
from typing import Callable, Generator, Any
from contextlib import contextmanager

from .ansi_interface import (
    save_cursor,
    restore_cursor,
    print_to,
    show_cursor,
    hide_cursor,
    do_echo,
    dont_echo,
    start_alt_buffer,
    end_alt_buffer,
)


@contextmanager
def cursor_at(pos: tuple[int, int]) -> Generator[Callable[..., None], None, None]:
    """Set cursor location to posx, posy, return function that
    prints there, incrementing the y value with each print."""

    offset = 0
    posx, posy = pos

    def printer(*args: tuple[Any, ...]) -> None:
        """Print to posx, current y"""

        nonlocal offset

        print_to((posx, posy + offset), *args)
        offset += 1

    try:
        save_cursor()
        yield printer

    finally:
        restore_cursor()


@contextmanager
def alt_buffer(echo: bool = False, cursor: bool = True) -> Generator[None, None, None]:
    """Create non-scrollable alt-buffer. Useful for retrieving original terminal state
    after program end."""

    try:
        start_alt_buffer()

        if not echo and name == "posix":
            dont_echo()

        if not cursor:
            hide_cursor()

        yield

    finally:
        end_alt_buffer()

        if not echo and name == "posix":
            do_echo()

        if not cursor:
            show_cursor()
