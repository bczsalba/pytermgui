"""This module houses the `Terminal` class, and its provided instance."""

from __future__ import annotations

import os
import sys
import signal
from enum import Enum
from typing import Any, Callable
from shutil import get_terminal_size

from .input import getch

__all__ = ["terminal", "ColorSystem"]


class ColorSystem(Enum):
    """An enumeration of various terminal-supported colorsystems."""

    NO_COLOR = -1
    """No-color terminal. See https://no-color.org/."""

    STANDARD = 0
    """Standard 3-bit colorsystem of the basic 16 colors."""

    EIGHT_BIT = 1
    """xterm 8-bit colors, 0-256."""

    TRUE = 2
    """'True' color, a.k.a. 24-bit RGB colors."""


def _get_env_colorsys() -> ColorSystem | None:
    """Gets a colorsystem if the `PTG_COLORSYS` env var can be linked to one."""

    colorsys = os.getenv("PTG_COLORSYS")
    if colorsys is None:
        return None

    try:
        return ColorSystem[colorsys]

    except NameError:
        return None


class Terminal:
    """A class to store & access data about a terminal."""

    RESIZE = 0
    """Event sent out when the terminal has been resized.

    Arguments passed:
    - New size: tuple[int, int]
    """

    margins = [0, 0, 0, 0]
    """Not quite sure what this does at the moment."""

    displayhook_installed: bool = False
    """This is set to True when `pretty.install` is called."""

    def __init__(self) -> None:
        """Initialize `_Terminal` class."""

        self.origin: tuple[int, int] = (1, 1)
        self.size: tuple[int, int] = self._get_size()
        self.forced_colorsystem: ColorSystem | None = _get_env_colorsys()
        self.pixel_size: tuple[int, int] = self._get_pixel_size()
        self._listeners: dict[int, list[Callable[..., Any]]] = {}

        if hasattr(signal, "SIGWINCH"):
            signal.signal(signal.SIGWINCH, self._update_size)

        # TODO: Support SIGWINCH on Windows.

    @staticmethod
    def _get_pixel_size() -> tuple[int, int]:
        """Gets the terminal's size, in pixels."""

        if sys.stdout.isatty():
            sys.stdout.write("\x1b[14t")
            sys.stdout.flush()

            # TODO: This probably should be error-proofed.
            output = getch()[4:-1]
            if ";" in output:
                size = tuple(int(val) for val in output.split(";"))
                return size[1], size[0]

        return (0, 0)

    def _call_listener(self, event: int, data: Any) -> None:
        """Calls callbacks for event.

        Args:
            event: A terminal event.
            data: Arbitrary data passed to the callback.
        """

        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(data)

    def _get_size(self) -> tuple[int, int]:
        """Gets the screen size with origin substracted."""

        size = get_terminal_size()
        return (size[0] - self.origin[0], size[1] - self.origin[1])

    def _update_size(self, *_: Any) -> None:
        """Resize terminal when SIGWINCH occurs, and call listeners."""

        self.size = self._get_size()
        self.pixel_size = self._get_pixel_size()
        self._call_listener(self.RESIZE, self.size)

    @property
    def width(self) -> int:
        """Gets the current width of the terminal."""

        return self.size[0]

    @property
    def height(self) -> int:
        """Gets the current height of the terminal."""

        return self.size[1]

    @staticmethod
    def is_interactive() -> bool:
        """Determines whether shell is interactive.

        A shell is interactive if it is run from `python3` or `python3 -i`.
        """

        return hasattr(sys, "ps1")

    def get_colorsystem(self) -> ColorSystem:
        """Gets the current terminal's supported color system."""

        if self.forced_colorsystem is not None:
            return self.forced_colorsystem

        if os.getenv("NO_COLOR") is not None:
            return ColorSystem.NO_COLOR

        color_term = os.getenv("COLORTERM", "").strip().lower()

        if color_term in ["24bit", "truecolor"]:
            return ColorSystem.TRUE

        if color_term == "256color":
            return ColorSystem.EIGHT_BIT

        return ColorSystem.STANDARD

    def subscribe(self, event: int, callback: Callable[..., Any]) -> None:
        """Subcribes a callback to be called when event occurs.

        Args:
            event: The terminal event that calls callback.
            callback: The callable to be called. The signature of this
                callable is dependent on the event. See the documentation
                of the specific event for more information.
        """

        if not event in self._listeners:
            self._listeners[event] = []

        self._listeners[event].append(callback)


terminal = Terminal()
"""Terminal instance that should be used pretty much always."""
