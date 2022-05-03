"""
Various functions to interface with the terminal, using ANSI sequences.

Credits:

- https://wiki.bash-hackers.org/scripting/terminalcodes
- https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""

# The entirety of Terminal will soon be moved over to a new submodule, so
# this ignore is temporary.
# pylint: disable=too-many-lines

from __future__ import annotations

import re

from typing import Optional, Any, Union, Pattern
from dataclasses import dataclass, fields
from enum import Enum, auto as _auto
from os import name as _name, system

from .input import getch
from .terminal import terminal

__all__ = [
    "save_screen",
    "restore_screen",
    "set_alt_buffer",
    "unset_alt_buffer",
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
    "set_echo",
    "unset_echo",
    "set_mode",
    "MouseAction",
    "MouseEvent",
    "report_mouse",
    "translate_mouse",
    "print_to",
    "reset",
    "bold",
    "dim",
    "italic",
    "underline",
    "blink",
    "inverse",
    "invisible",
    "strikethrough",
    "overline",
]


RE_MOUSE: dict[str, Pattern] = {
    "decimal_xterm": re.compile(r"<(\d{1,2})\;(\d{1,3})\;(\d{1,3})(\w)"),
    "decimal_urxvt": re.compile(r"(\d{1,2})\;(\d{1,3})\;(\d{1,3})()"),
}


# screen commands
def save_screen() -> None:
    """Saves the contents of the screen, and wipes it.

    Use `restore_screen()` to get them back.
    """

    print("\x1b[?47h")


def restore_screen() -> None:
    """Restores the contents of the screen saved by `save_screen()`."""

    print("\x1b[?47l")


def set_alt_buffer() -> None:
    """Starts an alternate buffer."""

    print("\x1b[?1049h")


def unset_alt_buffer() -> None:
    """Returns to main buffer, restoring its original state."""

    print("\x1b[?1049l")


def clear(what: str = "screen") -> None:
    """Clears the specified screen region.

    Args:
        what: The specifier defining the screen area.

    Available options:
    * screen: clear whole screen and go to origin
    * bos: clear screen from cursor backwards
    * eos: clear screen from cursor forwards
    * line: clear line and go to beginning
    * bol: clear line from cursor backwards
    * eol: clear line from cursor forwards
    """

    commands = {
        "eos": "\x1b[0J",
        "bos": "\x1b[1J",
        "screen": "\x1b[2J",
        "eol": "\x1b[0K",
        "bol": "\x1b[1K",
        "line": "\x1b[2K",
    }

    terminal.write(commands[what])


# cursor commands
def hide_cursor() -> None:
    """Stops printing the cursor."""

    print("\x1b[?25l")


def show_cursor() -> None:
    """Starts printing the cursor."""

    print("\x1b[?25h")


def save_cursor() -> None:
    """Saves the current cursor position.

    Use `restore_cursor()` to restore it.
    """

    terminal.write("\x1b[s")


def restore_cursor() -> None:
    """Restore cursor position as saved by `save_cursor`."""

    terminal.write("\x1b[u")


def report_cursor() -> tuple[int, int] | None:
    """Gets position of cursor.

    Returns:
        A tuple of integers, (columns, rows), describing the
        current (printing) cursor's position. Returns None if
        this could not be determined.

        Note that this position is **not** the mouse position. See
        `report_mouse` if that is what you are interested in.
    """

    print("\x1b[6n")
    chars = getch()
    posy, posx = chars[2:-1].split(";")

    if not posx.isdigit() or not posy.isdigit():
        return None

    return int(posx), int(posy)


def move_cursor(pos: tuple[int, int]) -> None:
    """Moves the cursor.

    Args:
        pos: Tuple of (columns, rows) that the cursor will be moved to.

    This does not flush the terminal for performance reasons. You
    can do it manually with `sys.stdout.flush()`.
    """

    posx, posy = pos
    terminal.write(f"\x1b[{posy};{posx}H")


def cursor_up(num: int = 1) -> None:
    """Moves the cursor up by `num` lines.

    Args:
        num: How many lines the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_down`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}A")


def cursor_down(num: int = 1) -> None:
    """Moves the cursor up by `num` lines.

    Args:
        num: How many lines the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_up`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}B")


def cursor_right(num: int = 1) -> None:
    """Moves the cursor right by `num` lines.

    Args:
        num: How many characters the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_left`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}C")


def cursor_left(num: int = 1) -> None:
    """Moves the cursor left by `num` lines.

    Args:
        num: How many characters the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_right`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """Moves the cursor to the beginning of the `num`-th line downwards.

    Args:
        num: The amount the cursor should move by. Must be positive, to move
            in the opposite direction use `cursor_prev_line`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """Moves the cursor to the beginning of the `num`-th line upwards.

    Args:
        num: The amount the cursor should move by. Must be positive, to move
            in the opposite direction use `cursor_next_line`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}F")


def cursor_column(num: int = 0) -> None:
    """Moves the cursor to the `num`-th character of the current line.

    Args:
        num: The new cursor position.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write(f"\x1b[{num}G")


def cursor_home() -> None:
    """Moves cursor to `terminal.origin`.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    terminal.write("\x1b[H")


def set_mode(mode: Union[str, int], write: bool = True) -> str:
    """Sets terminal display mode.

    This is better left internal. To use these modes, you can call their
    specific functions, such as `bold("text")` or `italic("text")`.

    Args:
        mode: One of the available modes. Strings and integers both work.
        write: Boolean that determines whether the output should be written
            to stdout.

    Returns:
        A string that sets the given mode.

    Available modes:
        - 0: reset
        - 1: bold
        - 2: dim
        - 3: italic
        - 4: underline
        - 5: blink
        - 7: inverse
        - 8: invisible
        - 9: strikethrough
        - 53: overline
    """

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
        "overline": 53,
    }

    if not str(mode).isdigit():
        mode = options[str(mode)]

    code = f"\x1b[{mode}m"
    if write:
        terminal.write(code)

    return code


def set_echo() -> None:
    """Starts echoing of user input.

    Note:
        This is currently only available on POSIX.
    """

    if not _name == "posix":
        return

    system("stty echo")


def unset_echo() -> None:
    """Stops echoing of user input.

    Note:
        This is currently only available on POSIX.
    """

    if not _name == "posix":
        return

    system("stty -echo")


class MouseAction(Enum):
    """An enumeration of all the polled mouse actions"""

    LEFT_CLICK = _auto()
    """Start of a left button action sequence."""

    LEFT_DRAG = _auto()
    """Mouse moved while left button was held down."""

    RIGHT_CLICK = _auto()
    """Start of a right button action sequence."""

    RIGHT_DRAG = _auto()
    """Mouse moved while right button was held down."""

    SCROLL_UP = _auto()
    """Mouse wheel or touchpad scroll upwards."""

    SCROLL_DOWN = _auto()
    """Mouse wheel or touchpad scroll downwards."""

    HOVER = _auto()
    """Mouse moved without clicking."""

    # TODO: Support left & right mouse release separately, without breaking
    #       current API.
    RELEASE = _auto()
    """Mouse button released; end of any and all mouse action sequences."""


@dataclass
class MouseEvent:
    """A class to represent events created by mouse actions.

    Its first argument is a `MouseAction` describing what happened,
    and its second argument is a `tuple[int, int]` describing where
    it happened.

    This class mostly exists for readability & typing reasons. It also
    implements the iterable protocol, so you can use the unpacking syntax,
    such as:

    ```python3
    action, position = MouseEvent(...)
    ```
    """

    action: MouseAction
    position: tuple[int, int]

    def __post_init__(self) -> None:
        """Initialize iteration counter"""

        self._iter_index = 0

    def __next__(self) -> MouseAction | tuple[int, int]:
        """Get next iteration item"""

        data = fields(self)

        if self._iter_index >= len(data):
            self._iter_index = 0
            raise StopIteration

        self._iter_index += 1
        return getattr(self, data[self._iter_index - 1].name)

    def __iter__(self) -> MouseEvent:
        """Start iteration"""

        return self

    def is_scroll(self) -> bool:
        """Returns True if event.action is one of the scrolling actions."""

        return self.action in {MouseAction.SCROLL_DOWN, MouseAction.SCROLL_UP}

    def is_primary(self) -> bool:
        """Returns True if event.action is one of the primary (left-button) actions."""

        return self.action in {MouseAction.LEFT_CLICK, MouseAction.LEFT_DRAG}

    def is_secondary(self) -> bool:
        """Returns True if event.action is one of the secondary (secondary-button) actions."""

        return self.action in {MouseAction.RIGHT_CLICK, MouseAction.RIGHT_DRAG}


def report_mouse(
    event: str, method: Optional[str] = "decimal_xterm", stop: bool = False
) -> None:
    """Starts reporting of mouse events.

    You can specify multiple events to report on.

    Args:
        event: The type of event to report on. See below for options.
        method: The method of reporting to use. See below for options.
        stop: If set to True, the stopping code is written to stdout.

    Raises:
        NotImplementedError: The given event is not supported.

    Note:
        If you need this functionality, you're probably better off using the wrapper
        `pytermgui.context_managers.mouse_handler`, which allows listening on multiple
        events, gives a translator method and handles exceptions.

    Possible events:
        - **press**: Report when the mouse is clicked, left or right button.
        - **highlight**: Report highlighting.
        - **press_hold**: Report with a left or right click, as well as both
            left & right drag and release.
        - **hover**: Report even when no active action is done, only the mouse
          is moved.

    Methods:
        - **None**: Non-decimal xterm method. Limited in coordinates.
        - **decimal_xterm**: The default setting. Most universally supported.
        - **decimal_urxvt**: Older, less compatible, but useful on some systems.
        - **decimal_utf8**:  Apparently not too stable.

    More information <a href='https://stackoverflow.com/a/5970472'>here</a>.
    """

    if event == "press":
        terminal.write("\x1b[?1000")

    elif event == "highlight":
        terminal.write("\x1b[?1001")

    elif event == "press_hold":
        terminal.write("\x1b[?1002")

    elif event == "hover":
        terminal.write("\x1b[?1003")

    else:
        raise NotImplementedError(f"Mouse report event {event} is not supported!")

    terminal.write("l" if stop else "h")

    if method == "decimal_utf8":
        terminal.write("\x1b[?1005")

    elif method == "decimal_xterm":
        terminal.write("\x1b[?1006")

    elif method == "decimal_urxvt":
        terminal.write("\x1b[?1015")

    elif method is None:
        return

    else:
        raise NotImplementedError(f"Mouse report method {method} is not supported!")

    terminal.write("l" if stop else "h", flush=True)


def translate_mouse(code: str, method: str) -> list[MouseEvent | None] | None:
    """Translates the output of produced by setting `report_mouse` into MouseEvents.

    This method currently only supports `decimal_xterm` and `decimal_urxvt`.

    Args:
        code: The string of mouse code(s) to translate.
        method: The reporting method to translate. One of [`decimal_xterm`, `decimal_urxvt`].

    Returns:
        A list of optional mouse events obtained from the code argument. If the code was malformed,
        and no codes could be determined None is returned.
    """

    if code == "\x1b":
        return None

    mouse_codes = {
        "decimal_xterm": {
            "0M": MouseAction.LEFT_CLICK,
            "0m": MouseAction.RELEASE,
            "2M": MouseAction.RIGHT_CLICK,
            "2m": MouseAction.RELEASE,
            "32": MouseAction.LEFT_DRAG,
            "34": MouseAction.RIGHT_DRAG,
            "35": MouseAction.HOVER,
            "64": MouseAction.SCROLL_UP,
            "65": MouseAction.SCROLL_DOWN,
        },
        "decimal_urxvt": {
            "32": MouseAction.LEFT_CLICK,
            "34": MouseAction.RIGHT_CLICK,
            "35": MouseAction.RELEASE,
            "64": MouseAction.LEFT_DRAG,
            "66": MouseAction.RIGHT_DRAG,
            "96": MouseAction.SCROLL_UP,
            "97": MouseAction.SCROLL_DOWN,
        },
    }

    mapping = mouse_codes[method]
    pattern: Pattern = RE_MOUSE[method]

    events: list[MouseEvent | None] = []

    for sequence in code.split("\x1b"):
        if len(sequence) == 0:
            continue

        matches = list(pattern.finditer(sequence))
        if len(matches) == 0:
            return None

        for match in matches:
            identifier, *pos, release_code = match.groups()

            # decimal_xterm uses the last character's
            # capitalization to signify press/release state
            if len(release_code) > 0 and identifier in ["0", "2"]:
                identifier += release_code

            if identifier in mapping:
                action = mapping[identifier]
                assert isinstance(action, MouseAction)

                events.append(MouseEvent(action, (int(pos[0]), int(pos[1]))))
                continue

            events.append(None)

    return events


# shorthand functions
def print_to(pos: tuple[int, int], *args: Any, **kwargs: Any) -> None:
    """Prints text to given `pos`.

    Note:
        This method passes through all arguments (except for `pos`) to the `print`
        method.
    """

    move_cursor(pos)
    print(*args, **kwargs, end="", flush=True)


def reset() -> str:
    """Resets printing mode."""

    return set_mode("reset", False)


def bold(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text in bold.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("bold", False) + text + (reset() if reset_style else "")


def dim(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text in dim.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("dim", False) + text + (reset() if reset_style else "")


def italic(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text in italic.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("italic", False) + text + (reset() if reset_style else "")


def underline(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text underlined.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("underline", False) + text + (reset() if reset_style else "")


def blink(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text blinking.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("blink", False) + text + (reset() if reset_style else "")


def inverse(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text inverse-colored.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("inverse", False) + text + (reset() if reset_style else "")


def invisible(text: str, reset_style: Optional[bool] = True) -> str:
    """Returns text as invisible.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.

    Note:
        This isn't very widely supported.
    """

    return set_mode("invisible", False) + text + (reset() if reset_style else "")


def strikethrough(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text as strikethrough.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.
    """

    return set_mode("strikethrough", False) + text + (reset() if reset_style else "")


def overline(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text overlined.

    Args:
        reset_style: Boolean that determines whether a reset character should
            be appended to the end of the string.

    Note:
        This isnt' very widely supported.
    """

    return set_mode("overline", False) + text + (reset() if reset_style else "")
