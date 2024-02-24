"""This module lets you run widgets as an inline terminal prompt."""

from __future__ import annotations

from typing import TypeVar

from ..ansi_interface import (
    clear,
    hide_cursor,
    print_to,
    report_cursor,
    restore_cursor,
    save_cursor,
    set_echo,
    show_cursor,
    unset_echo,
)
from ..context_managers import mouse_handler
from ..input import getch, keys
from ..term import get_terminal
from .base import Widget

T = TypeVar("T", bound=Widget)


def inline(
    widget: T, *, exit_on: list[str] | None = None, width: int | None = None
) -> T:
    """Runs a widget as an inline terminal prompt.

    This can be useful for adding GUI-like functionality within CLI scripts, as it
    gives you access to the widget system for building prompts, built in keyboard &
    mouse handling and everything else that makes PyTermGUI's WindowManager work,
    without the commitment to a full-screen app.

    Args:
        widget: Some widget that will be run.
        width: The width to set for the widget. If nothing is given, the widget's
            width is unchanged.

    Returns:
        The same widget. This allows defining and running a prompt in the same line:

            ```python
            prompt = inline(_build_prompt())
            ```
    """

    # Make sure we use the global terminal
    terminal = get_terminal()

    unset_echo()
    hide_cursor()

    if width is not None:
        widget.width = width

    if exit_on is None:
        exit_on = [keys.CTRL_C, keys.ENTER]

    cursor = report_cursor()

    if cursor is not None:
        widget.pos = cursor

    def _print_widget() -> None:
        save_cursor()

        for line in widget.get_lines():
            print(line)

        for pos, line in widget.positioned_line_buffer:
            print_to(pos, line)
        widget.positioned_line_buffer = []

        restore_cursor()

    def _clear_widget() -> None:
        save_cursor()

        for _ in range(widget.height):
            clear("line")
            terminal.write("\n")

        restore_cursor()
        terminal.flush()

    _print_widget()

    with mouse_handler(["all"], "decimal_xterm") as translate:
        while True:
            key = getch(interrupts=False)

            if key in exit_on:
                break

            if not widget.handle_key(key):
                events = translate(key)
                # Don't try iterating when there are no events
                if events is None:
                    continue

                for event in events:
                    if event is None:
                        continue
                    widget.handle_mouse(event)

            _clear_widget()
            _print_widget()

    _clear_widget()

    set_echo()
    show_cursor()

    return widget
