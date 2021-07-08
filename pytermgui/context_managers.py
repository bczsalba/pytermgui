"""
pytermgui.context_managers
--------------------------
author: bczsalba


Module providing context-manager classes & functions.

There isn't much (or any) additional functionality provided
in this module, most things are nicer-packaged combinations to
already available methods from ansi_interface.
"""

from os import name
from typing import Callable, Generator, Any, Optional
from contextlib import contextmanager

from .ansi_interface import (
    is_interactive,
    save_cursor,
    restore_cursor,
    print_to,
    show_cursor,
    hide_cursor,
    do_echo,
    dont_echo,
    start_alt_buffer,
    end_alt_buffer,
    cursor_up,
    report_mouse,
    translate_mouse,
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

        if not echo and name == "posix" and not is_interactive():
            dont_echo()

        if not cursor:
            hide_cursor()

        yield

    finally:
        end_alt_buffer()

        if not echo and name == "posix" and not is_interactive():
            do_echo()
            cursor_up()

        if not cursor:
            show_cursor()
            cursor_up()


@contextmanager
def mouse_handler(
    event: str,
) -> Generator[Callable[[str], Optional[tuple[bool, tuple[int, int]]]], None, None]:
    """Return a mouse handler function

    Note: This only supports the method `decimal_xterm` as it seems to be the most universal,
    and has one of the nicer interfaces.

    Example use:
        >>> from pytermgui import mouse_handler, getch
        >>> with mouse_handler("press") as mouse:
        ...     while True:
        ...         event = mouse(getch())
        '(True, (33, 55))'
    """

    try:
        report_mouse(event, method="decimal_xterm")
        yield translate_mouse

    finally:
        report_mouse(event, method="decimal_xterm", action="stop")
