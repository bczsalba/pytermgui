"""
Ease-of-use context-manager classes & functions.

There isn't much (or any) additional functionality provided in this module,
most things are nicer-packaged combinations to already available methods from
`pytermgui.ansi_interface`.
"""

from __future__ import annotations

from contextlib import contextmanager
from os import name
from typing import Any, Callable, Generator, List, Union

from .ansi_interface import (
    MouseEvent,
    cursor_up,
    hide_cursor,
    print_to,
    report_mouse,
    restore_cursor,
    save_cursor,
    set_alt_buffer,
    set_echo,
    show_cursor,
    translate_mouse,
    unset_alt_buffer,
    unset_echo,
)

# This is technically meant to be here, but it has to be in `input.py` due
# to some package structure issues.
from .input import timeout  # pylint: disable=unused-import
from .term import get_terminal

# TODO: Move this absolute beast to a types submodule
MouseTranslator = Callable[[str], Union[List[Union[MouseEvent, None]], None]]


@contextmanager
def cursor_at(pos: tuple[int, int]) -> Generator[Callable[..., None], None, None]:
    """Gets callable to print at `pos`, incrementing `y` on every print.

    Args:
        pos: The position to start printing at. Follows the order (columns, rows).

    Yields:
        A callable printing function. This function forwards all arguments to `print`,
        but positions the cursor before doing so. After every call, the y position is
        incremented.
    """

    offset = 0
    posx, posy = pos

    def printer(*args: Any, **kwargs: Any) -> None:
        """Print to posx, current y"""

        nonlocal offset

        print_to((posx, posy + offset), *args, **kwargs)
        offset += 1

    try:
        save_cursor()
        yield printer

    finally:
        restore_cursor()


@contextmanager
def alt_buffer(echo: bool = False, cursor: bool = True) -> Generator[None, None, None]:
    """Creates non-scrollable alt-buffer.

    This is useful for retrieving original terminal state after program end.

    Args:
        echo: Whether `unset_echo` should be called on startup.
        cursor: Whether `hide_cursor` should be called on startup.
    """

    terminal = get_terminal()

    try:
        set_alt_buffer()

        if not echo and name == "posix" and not terminal.is_interactive():
            unset_echo()

        if not cursor:
            hide_cursor()

        yield

    finally:
        unset_alt_buffer()

        if not echo and name == "posix" and not terminal.is_interactive():
            set_echo()
            cursor_up()

        if not cursor:
            show_cursor()
            cursor_up()


@contextmanager
def mouse_handler(
    events: list[str], method: str = "decimal_xterm"
) -> Generator[MouseTranslator, None, None]:
    """Return a mouse handler function

    See `help(report_mouse)` for help about all of the methods.

    Args:
        events: A list of `pytermgui.ansi_interface.report_mouse` events.
        method: The method to use for reporting. Only `decimal_urxvt` and
            `decimal_xterm` are currently supported.

    Example use:

    ```python3
    import pytermgui as ptg

    with ptg.mouse_handler(["press", "hover"]) as mouse:
        while True:
          event = mouse(ptg.getch())
          print(type(event))
          print(event.action)
          print(event.position)

    'pytermgui.ansi_interface.MouseEvent'
    'pytermgui.ansi_interface.MouseAction.LEFT_CLICK'
    (33, 55)
    ```

    """

    try:
        for event in events:
            report_mouse(event, method=method)

        yield lambda code: translate_mouse(code, method=method)

    finally:
        for event in events:
            report_mouse(event, method=method, stop=True)
