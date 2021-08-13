"""
pytermgui.ansi_interface
------------------------
author: bczsalba


Various functions to interface with the terminal, using ANSI sequences.
Note:
    While most of these are universal on all modern terminals, there might
    be some that don't always work. I'll try to mark these separately.

    Also, using the escape sequence for save/restore of terminal doesn't work,
    only tput does. We should look into that.

Credits:
    - https://wiki.bash-hackers.org/scripting/terminalcodes
    - https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""

from __future__ import annotations

import re
import sys

from typing import Optional, Any, Union, Tuple
from enum import Enum, auto as _auto
from sys import stdout as _stdout
from string import hexdigits
from subprocess import (
    run as _run,
    Popen as _Popen,
)
from os import (
    name as _name,
    get_terminal_size,
    system,
)
from .input import getch


__all__ = [
    "foreground",
    "background",
    "is_interactive",
    "screen_size",
    "screen_width",
    "screen_height",
    "save_screen",
    "restore_screen",
    "start_alt_buffer",
    "end_alt_buffer",
    "clear",
    "hide_cursor",
    "show_cursor",
    "save_cursor",
    "restore_cursor",
    "report_cursor",
    "move_cursor",
    "cursor_up",
    "cursor_down",
    "cursor_right",
    "cursor_left",
    "cursor_next_line",
    "cursor_prev_line",
    "cursor_column",
    "cursor_home",
    "do_echo",
    "dont_echo",
    "set_mode",
    "MouseAction",
    "report_mouse",
    "translate_mouse",
    "print_to",
    "reset",
    "bold",
    "dim",
    "italic",
    "underline",
    "blinking",
    "inverse",
    "invisible",
    "strikethrough",
    "fill_window",
]


class _Color:
    """Parent class for Color objects"""

    def __init__(self, layer: int = 0) -> None:
        """Set layer"""

        if layer not in [0, 1]:
            raise NotImplementedError(
                f"Layer {layer} is not supported for Color256 objects! Please choose from 0, 1"
            )

        self.names = {
            "black": 0,
            "red": 1,
            "green": 2,
            "yellow": 3,
            "blue": 4,
            "magenta": 5,
            "cyan": 6,
            "white": 7,
        }

        self.layer_offset = layer * 10

    @staticmethod
    def translate_hex(color: str) -> tuple[int, int, int]:
        """Translate hex string to rgb values"""

        if color.startswith("#"):
            color = color[1:]

        rgb = []
        for i in (0, 2, 4):
            color_hex = color[i : i + 2]
            rgb.append(int(color_hex, 16))

        return rgb[0], rgb[1], rgb[2]

    def __call__(
        self,
        text: str,
        color: Union[
            int, str, tuple[Union[int, str], Union[int, str], Union[int, str]]
        ],
        reset_color: bool = True,
    ) -> str:
        """Return colored text with reset code at the end"""

        # convert hex string to tuple[int, int, int]
        if isinstance(color, str) and all(
            char in hexdigits or char == "#" for char in color
        ):
            try:
                color = self.translate_hex(color)
            except ValueError:
                # value is not a hex number, but is string
                pass

        if color in self.names:
            new = self.names[str(color)]
            assert isinstance(new, int)
            color = new

        # rgb values
        if isinstance(color, tuple):
            red, green, blue = color
            color_value = f"2;{red};{green};{blue}m"

        # 8-bit colors (including 0-16)
        elif isinstance(color, int) or color.isdigit():
            color_value = f"5;{color}m"

        else:
            raise NotImplementedError(
                f"Not sure what to do with {color} of type {type(color)}"
            )

        return (
            f"\x1b[{38 + self.layer_offset};"
            + color_value
            + text
            + (set_mode("reset") if reset_color else "")
        )


foreground = _Color()
background = _Color(layer=1)


# helpers
def _tput(command: list[str]) -> None:
    """Shorthand for tput calls"""

    waited_commands = [
        "clear",
        "smcup",
        "cup",
    ]

    command.insert(0, "tput")
    str_command = [str(c) for c in command]

    if command[1] in waited_commands:
        _run(str_command, check=True)
        return

    _Popen(str_command)


def is_interactive() -> bool:
    """Check if shell is interactive (`python3` or `python3 -i`)"""

    return hasattr(sys, "ps1")


# screen commands
def screen_size() -> tuple[int, int]:
    """Get screen size using os module

    This is technically possible using a method of
    moving the cursor to an impossible location, and
    using `report_cursor()` to get where the position
    was clamped, but it messes with the cursor position
    and makes for glitchy printing.
    """

    # TODO: Add SIGWINCH handling

    return get_terminal_size()


def screen_width() -> int:
    """Get screen width"""

    size = screen_size()

    if size is None:
        return 0
    return size[0]


def screen_height() -> int:
    """Get screen height"""

    size = screen_size()

    if size is None:
        return 0
    return size[1]


def save_screen() -> None:
    """Save the contents of the screen, wipe.
    Use `restore_screen()` to get them back."""

    # print("\x1b[?47h")
    _tput(["smcup"])


def restore_screen() -> None:
    """Restore the contents of the screen,
    previously saved by a call to `save_screen()`."""

    # print("\x1b[?47l")
    _tput(["rmcup"])


def start_alt_buffer() -> None:
    """Start alternate buffer that is non-scrollable"""

    print("\x1b[?1049h")


def end_alt_buffer() -> None:
    """Return to main buffer from alt, restoring state"""

    print("\x1b[?1049l")


def clear(what: str = "screen") -> None:
    """Clear specified region

    Available options:
        - screen - clear whole screen and go home
        - bos    - clear screen from cursor backwards
        - eos    - clear screen from cursor forwards
        - line   - clear line and go to beginning
        - bol    - clear line from cursor backwards
        - eol    - clear line from cursor forwards

    """

    commands = {
        "eos": "\x1b[0J",
        "bos": "\x1b[1J",
        "screen": "\x1b[2J",
        "eol": "\x1b[0K",
        "bol": "\x1b[1K",
        "line": "\x1b[2K",
    }

    _stdout.write(commands[what])


# cursor commands
def hide_cursor() -> None:
    """Don't print cursor"""

    # _tput(['civis'])
    print("\x1b[?25l")


def show_cursor() -> None:
    """Set cursor printing back on"""

    # _tput(['cvvis'])
    print("\x1b[?25h")


def save_cursor() -> None:
    """Save cursor position, use `restore_cursor()`
    to restore it."""

    # _tput(['sc'])
    _stdout.write("\x1b[s")


def restore_cursor() -> None:
    """Restore cursor position saved by `save_cursor()`"""

    # _tput(['rc'])
    _stdout.write("\x1b[u")


def report_cursor() -> Optional[tuple[int, int]]:
    """Get position of cursor"""

    print("\x1b[6n")
    chars = getch()
    posy, posx = chars[2:-1].split(";")

    if not posx.isdigit() or not posy.isdigit():
        return None

    return int(posx), int(posy)


def move_cursor(pos: tuple[int, int]) -> None:
    """Move cursor to pos"""

    posx, posy = pos
    _stdout.write(f"\x1b[{posy};{posx}H")


def cursor_up(num: int = 1) -> None:
    """Move cursor up by `num` lines"""

    _stdout.write(f"\x1b[{num}A")


def cursor_down(num: int = 1) -> None:
    """Move cursor down by `num` lines"""

    _stdout.write(f"\x1b[{num}B")


def cursor_right(num: int = 1) -> None:
    """Move cursor left by `num` cols"""

    _stdout.write(f"\x1b[{num}C")


def cursor_left(num: int = 1) -> None:
    """Move cursor left by `num` cols"""

    _stdout.write(f"\x1b[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """Move cursor to beginning of num-th line down"""

    _stdout.write(f"\x1b[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """Move cursor to beginning of num-th line down"""

    _stdout.write(f"\x1b[{num}F")


def cursor_column(num: int = 0) -> None:
    """Move cursor to num-th column in the current line"""

    _stdout.write(f"\x1b[{num}G")


def cursor_home() -> None:
    """Move cursor to HOME"""

    _stdout.write("\x1b[H")


def set_mode(mode: Union[str, int], write: bool = True) -> str:
    """Set terminal display mode

    Available options:
        - reset         (0)
        - bold          (1)
        - dim           (2)
        - italic        (3)
        - underline     (4)
        - blink         (5)
        - inverse       (7)
        - invisible     (8)
        - strikethrough (9)

    You can use both the digit and text forms."""

    options = {
        "reset": 0,
        "bold": 1,
        "dim": 2,
        "italic": 3,
        "underline": 4,
        "blink": 5,
        "inverse": 7,
        "invisible": 8,
        "strikethrough": 9,
    }

    if not str(mode).isdigit():
        mode = options[str(mode)]

    code = f"\x1b[{mode}m"
    if write:
        _stdout.write(code)

    return code


def do_echo() -> None:
    """Echo user input"""

    if not _name == "posix":
        raise NotImplementedError("This method is only implemented on POSIX systems.")

    system("stty echo")


def dont_echo() -> None:
    """Don't echo user input"""

    if not _name == "posix":
        raise NotImplementedError("This method is only implemented on POSIX systems.")

    system("stty -echo")


class MouseAction(Enum):
    """Actions a mouse can perform"""

    HOLD = _auto()
    PRESS = _auto()
    HOVER = _auto()
    RELEASE = _auto()
    SCROLL_UP = _auto()
    SCROLL_DOWN = _auto()
    RIGHT_HOLD = _auto()
    RIGHT_PRESS = _auto()


MouseEvent = Tuple[MouseAction, Tuple[int, int]]


def report_mouse(
    event: str, method: Optional[str] = "decimal_xterm", stop: bool = False
) -> None:
    """Start reporting mouse events

    options:
        - press
        - highlight
        - press_hold
        - hover

    methods:
        None:          limited in coordinates, not recommended.
        decimal_xterm: default, most universal
        decimal_urxvt: older, less compatible
        decimal_utf8:  apparently not too stable

    more information: https://stackoverflow.com/a/5970472
    """

    if event == "press":
        _stdout.write("\x1b[?1000")

    elif event == "highlight":
        _stdout.write("\x1b[?1001")

    elif event == "press_hold":
        _stdout.write("\x1b[?1002")

    elif event == "hover":
        _stdout.write("\x1b[?1003")

    else:
        raise NotImplementedError(f"Mouse report event {event} is not supported!")

    _stdout.write("l" if stop else "h")

    if method == "decimal_utf8":
        _stdout.write("\x1b[?1005")

    elif method == "decimal_xterm":
        _stdout.write("\x1b[?1006")

    elif method == "decimal_urxvt":
        _stdout.write("\x1b[?1015")

    elif method is None:
        return

    else:
        raise NotImplementedError(f"Mouse report method {method} is not supported!")

    _stdout.write("l" if stop else "h")
    _stdout.flush()


def translate_mouse(code: str, method: str) -> Optional[list[Optional[MouseEvent]]]:
    """Translate report_mouse() (decimal_xterm or decimal_urxvt) codes into
    tuple[action, tuple[x, y]].

    See `help(report_mouse)` for more information on methods."""

    mouse_codes = {
        "decimal_xterm": {
            "pattern": re.compile(r"<(\d{1,2})\;(\d{1,3})\;(\d{1,3})(\w)"),
            "0M": MouseAction.PRESS,
            "0m": MouseAction.RELEASE,
            "2": MouseAction.RIGHT_PRESS,
            "32": MouseAction.HOLD,
            "34": MouseAction.RIGHT_HOLD,
            "35": MouseAction.HOVER,
            "66": MouseAction.RIGHT_HOLD,
            "64": MouseAction.SCROLL_UP,
            "65": MouseAction.SCROLL_DOWN,
        },
        "decimal_urxvt": {
            "pattern": re.compile(r"(\d{1,2})\;(\d{1,3})\;(\d{1,3})()"),
            "32": MouseAction.PRESS,
            "34": MouseAction.RIGHT_PRESS,
            "35": MouseAction.RELEASE,
            "64": MouseAction.HOLD,
            "66": MouseAction.RIGHT_HOLD,
            "96": MouseAction.SCROLL_UP,
            "97": MouseAction.SCROLL_DOWN,
        },
    }

    mapping = mouse_codes[method]
    pattern = mapping["pattern"]

    events: list[Optional[tuple[MouseAction, tuple[int, int]]]] = []
    for sequence in code.split("\x1b"):
        if len(sequence) == 0:
            continue

        matches = list(pattern.finditer(sequence))
        if matches == []:
            return None

        for match in matches:
            identifier, *pos, release_code = match.groups()

            # decimal_xterm uses the last character's
            # capitalization to signify press/release state
            if len(release_code) > 0 and identifier == "0":
                identifier += release_code

            if identifier in mapping:
                action = mapping[identifier]
                assert isinstance(action, MouseAction)

                events.append((action, (int(pos[0]), int(pos[1]))))
                continue

            events.append(None)

    return events


# shorthand functions
def print_to(pos: tuple[int, int], *args: tuple[Any, ...]) -> None:
    """Print text to given position"""

    text = ""
    for arg in args:
        text += " " + str(arg)

    move_cursor(pos)
    print(text)


def reset() -> str:
    """Reset printing mode"""

    return set_mode("reset", False)


def bold(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text in bold"""

    return set_mode("bold", False) + text + (reset() if reset_style else "")


def dim(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text in dim"""

    return set_mode("dim", False) + text + (reset() if reset_style else "")


def italic(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text in italic"""

    return set_mode("italic", False) + text + (reset() if reset_style else "")


def underline(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text underlined"""

    return set_mode("underline", False) + text + (reset() if reset_style else "")


def blinking(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text blinking"""

    return set_mode("blink", False) + text + (reset() if reset_style else "")


def inverse(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text inverse-colored"""

    return set_mode("inverse", False) + text + (reset() if reset_style else "")


def invisible(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text in invisible"""

    return set_mode("invisible", False) + text + (reset() if reset_style else "")


def strikethrough(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text as strikethrough"""

    return set_mode("strikethrough", False) + text + (reset() if reset_style else "")


def fill_window(color: int, flush: bool = True) -> None:
    """Fill window with a color"""

    for i in range(screen_height()):
        _stdout.write(background(screen_width() * " ", color))
        if not i == screen_height() - 1:
            _stdout.write("\n")

    if flush:
        _stdout.flush()
