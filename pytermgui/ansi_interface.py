"""
Various functions to interface with the terminal, using ANSI sequences.

Credits:

- https://wiki.bash-hackers.org/scripting/terminalcodes
- https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""

from __future__ import annotations

import re
import sys
import signal

from typing import Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, fields
from enum import Enum, auto as _auto
from sys import stdout as _stdout
from string import hexdigits
from subprocess import run as _run, Popen as _Popen
from os import name as _name, get_terminal_size, system

from .input import getch


__all__ = [
    "Color",
    "foreground",
    "background",
    "terminal",
    "is_interactive",
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
]


class Color:
    """Class to store various color utilities

    Two instances of this class are provided, `foreground`
    and `background`. The difference between these is the color
    layer they operate on.

    To use this class you should call either instances with some
    data type representing a color. The following patterns are supported:

    - `int`: 0-256 terminal colors
    - `str`: Name of one of the registered named colors. See `Color.names`.
    - `#rrggbb`: RGB hex string. Note: alpha values are not supported.
    - `tuple[int, int]`: Tuple of RGB colors, each 0-256.
    """

    ColorType = Union[int, str, Tuple[int, int, int]]
    """A simple type to represent color patterns. See `Color` for more info."""

    names = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
        "grey": 8,
        "brightred": 9,
        "brightgreen": 10,
        "brightyellow": 11,
        "brightblue": 12,
        "brightmagenta": 13,
        "brightcyan": 14,
        "brightwhite": 15,
    }
    """16 default named colors. Expanding this list will expand the names `pytermgui.parser.markup`
    will recognize, but if that is your objective it is better to use
    `pytermgui.parser.MarkupLanguage.alias`."""

    def __init__(self, layer: int = 0) -> None:
        """Initialize object

        `layer` can be either 0 or 1. This value determines whether the instance
        will represent foreground or background colors."""

        if layer not in [0, 1]:
            raise NotImplementedError(f"Layer {layer} can only be one of [0, 1].")

        self.layer_offset = layer * 10

    @staticmethod
    def translate_hex(color: str) -> tuple[int, int, int]:
        """Translate hex string of format #RRGGBB into an RGB tuple of integers"""

        if color.startswith("#"):
            color = color[1:]

        rgb = []
        for i in (0, 2, 4):
            color_hex = color[i : i + 2]
            rgb.append(int(color_hex, 16))

        return rgb[0], rgb[1], rgb[2]

    def __call__(self, text: str, color: ColorType, reset_color: bool = True) -> str:
        """Color a piece of text using `color`.

        The color can be one of 4 formats:
            - str colorname:   One of the predifined named colors. See the names dict.
            - int 0-256:       One of the 256 terminal colors.
            - str #RRGGBB:     CSS-style HEX string, without alpha.
            - tuple (0-256, 0-256, 0-256): Tuple of integers, representing an RGB color.

        If `reset_color` is set a reset sequence is inserted at the end."""

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


foreground = Color()
"""`Color` instance to setting foreground colors"""

background = Color(layer=1)
"""`Color` instance to setting background colors"""


def screen_size() -> tuple[int, int]:
    """Get screen size using the os module

    This is technically possible using a method of moving the
    cursor to an impossible location, and using `report_cursor()`
    to get where the position was clamped. This however messes
    with the cursor position and printing gets a bit glitchy."""

    try:
        width, height = get_terminal_size()
        return (width, height)

    except OSError as error:
        if error.errno != 25:
            raise
        return 0, 0


class _Terminal:
    """A class to store & access data about a terminal"""

    RESIZE = 0
    margins = [0, 0, 0, 0]

    def __init__(self) -> None:
        """Initialize object"""

        self.origin: tuple[int, int] = (1, 1)
        self.size: tuple[int, int] = self._get_size()
        self._listeners: dict[int, list[Callable[..., Any]]] = {}

        # TODO: Windows doesn't support SIGWINCH, is there another alternative?
        if not _name == "nt":
            signal.signal(signal.SIGWINCH, self._update_size)

    def _call_listener(self, event: int, data: Any) -> None:
        """Call event callback is one is found."""

        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(data)

    def _get_size(self) -> tuple[int, int]:
        """Get screen size while substracting the origin position"""

        # This always has len() == 2, but mypy can't see that.
        return tuple(val - org for val, org in zip(screen_size(), self.origin))  # type: ignore

    def _update_size(self, *_: Any) -> None:
        """Resize terminal when SIGWINCH occurs.

        Note:
            SIGWINCH is not supported on Windows, so this isn't called."""

        self.size = self._get_size()
        self._call_listener(self.RESIZE, self.size)

    @property
    def width(self) -> int:
        """Get width of terminal"""

        return self.size[0]

    @property
    def height(self) -> int:
        """Get height of terminal"""

        return self.size[1]

    def subscribe(self, event: int, callback: Callable[..., Any]) -> None:
        """Subscribe a callback function to an event

        The callback takes an event-specific argument payload:
            RESIZE: tuple[int, int] - New screen size"""

        if not event in self._listeners:
            self._listeners[event] = []

        self._listeners[event].append(callback)

    def fill(self, color: int = 0, flush: bool = True) -> None:
        """Fill entire terminal with a color"""

        for height in range(self.height):
            sys.stdout.write(
                f"\033[{height};0H" + background(" " * (self.width - 1), color)
            )

        if flush:
            sys.stdout.flush()


terminal = _Terminal()

# helpers
def _tput(command: list[str]) -> None:
    """Shorthand for tput calls"""

    waited_commands = ["clear", "smcup", "cup"]

    command.insert(0, "tput")
    str_command = [str(c) for c in command]

    if command[1] in waited_commands:
        _run(str_command, check=True)
        return

    # A with statement here would result in `pass`, so is unnecessary.
    _Popen(str_command)  # pylint: disable=consider-using-with


def is_interactive() -> bool:
    """Determine whether shell is interactive.

    A shell is interactive if it is run from `python3` or `python3 -i`."""

    return hasattr(sys, "ps1")


# screen commands
def save_screen() -> None:
    """Save the contents of the screen, wipe.

    Use `restore_screen()` to get them back."""

    # print("\x1b[?47h")
    _tput(["smcup"])


def restore_screen() -> None:
    """Restore the contents of the screen saved by `save_screen()`"""

    # print("\x1b[?47l")
    _tput(["rmcup"])


def set_alt_buffer() -> None:
    """Start alternate buffer

    Note: This buffer is unscrollable."""

    print("\x1b[?1049h")


def unset_alt_buffer() -> None:
    """Return to main buffer from alt, restoring its original state"""

    print("\x1b[?1049l")


def clear(what: str = "screen") -> None:
    """Clear specified region

    Available options:
    - `screen` - clear whole screen and go to origin
    - `bos` - clear screen from cursor backwards
    - `eos` - clear screen from cursor forwards
    - `line` - clear line and go to beginning
    - `bol` - clear line from cursor backwards
    - `eol` - clear line from cursor forwards

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
    """Stop printing cursor"""

    # _tput(['civis'])
    print("\x1b[?25l")


def show_cursor() -> None:
    """Start printing cursor"""

    # _tput(['cvvis'])
    print("\x1b[?25h")


def save_cursor() -> None:
    """Save cursor position.

    Use `restore_cursor()` to restore it."""

    # _tput(['sc'])
    _stdout.write("\x1b[s")


def restore_cursor() -> None:
    """Restore cursor position saved by `save_cursor()`"""

    # _tput(['rc'])
    _stdout.write("\x1b[u")


def report_cursor() -> tuple[int, int] | None:
    """Get position of cursor"""

    print("\x1b[6n")
    chars = getch()
    posy, posx = chars[2:-1].split(";")

    if not posx.isdigit() or not posy.isdigit():
        return None

    return int(posx), int(posy)


def move_cursor(pos: tuple[int, int]) -> None:
    """Move cursor to `pos`.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    posx, posy = pos
    _stdout.write(f"\x1b[{posy};{posx}H")


def cursor_up(num: int = 1) -> None:
    """Move cursor up by `num` lines.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}A")


def cursor_down(num: int = 1) -> None:
    """Move cursor down by `num` lines.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}B")


def cursor_right(num: int = 1) -> None:
    """Move cursor left by `num` cols.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}C")


def cursor_left(num: int = 1) -> None:
    """Move cursor left by `num` cols.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """Move cursor to beginning of `num`-th line down.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """Move cursor to beginning of `num`-th line down.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}F")


def cursor_column(num: int = 0) -> None:
    """Move cursor to `num`-th column in the current line.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write(f"\x1b[{num}G")


def cursor_home() -> None:
    """Move cursor to `terminal.origin`.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`."""

    _stdout.write("\x1b[H")


def set_mode(mode: Union[str, int], write: bool = True) -> str:
    """Set terminal display mode

    Available options:
    - 0 - `reset`
    - 1 - `bold`
    - 2 - `dim`
    - 3 - `italic`
    - 4 - `underline`
    - 5 - `blink`
    - 7 - `inverse`
    - 8 - `invisible`
    - 9 - `strikethrough`

    You can use both the digit and text forms, though you should really be
    using one of the specific setters, like `bold` or `italic`."""

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


def set_echo() -> None:
    """Start echoing user input"""

    if not _name == "posix":
        raise NotImplementedError("This method is only implemented on POSIX systems.")

    system("stty echo")


def unset_echo() -> None:
    """Stop echoing user input"""

    if not _name == "posix":
        raise NotImplementedError("This method is only implemented on POSIX systems.")

    system("stty -echo")


class MouseAction(Enum):
    """An enumeration of all the polled mouse actions"""

    LEFT_CLICK = _auto()
    """Start of a left button action sequence"""

    LEFT_DRAG = _auto()
    """Mouse moved while left button was held down"""

    RIGHT_CLICK = _auto()
    """Start of a right button action sequence"""

    RIGHT_DRAG = _auto()
    """Mouse moved while right button was held down"""

    SCROLL_UP = _auto()
    """Mouse wheel or touchpad scroll upwards"""

    SCROLL_DOWN = _auto()
    """Mouse wheel or touchpad scroll downwards"""

    HOVER = _auto()
    """Mouse moved without clicking

    Note: This only gets registered when hover events are listened to"""

    RELEASE = _auto()
    """Mouse button released; end of any and all mouse action sequences"""


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


def report_mouse(
    event: str, method: Optional[str] = "decimal_xterm", stop: bool = False
) -> None:
    """Start reporting mouse events.

    Options:
    - `press`
    - `highlight`
    - `press_hold`
    - `hover`

    Methods:
    - `None`:          Limited in coordinates, not recommended.
    - `decimal_xterm`: Default, most universal
    - `decimal_urxvt`: Older, less compatible
    - `decimal_utf8`:  Apparently not too stable

    More information <a href='https://stackoverflow.com/a/5970472'>here</a>.

    Note:
        If you need this functionality, you're probably better off using the wrapper
        `pytermgui.context_managers.mouse_handler`, which allows listening on multiple
        events, gives a translator method and handles exceptions.
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


def translate_mouse(code: str, method: str) -> list[MouseEvent | None] | None:
    """Translate the output of produced by setting report_mouse codes into MouseEvent-s.

    This currently only supports `decimal_xterm` and `decimal_urvxt`. See `report_mouse` for more
    information."""

    mouse_codes = {
        "decimal_xterm": {
            "pattern": re.compile(r"<(\d{1,2})\;(\d{1,3})\;(\d{1,3})(\w)"),
            "0M": MouseAction.LEFT_CLICK,
            "0m": MouseAction.RELEASE,
            "2": MouseAction.RIGHT_CLICK,
            "32": MouseAction.LEFT_DRAG,
            "34": MouseAction.RIGHT_DRAG,
            "35": MouseAction.HOVER,
            "64": MouseAction.SCROLL_UP,
            "65": MouseAction.SCROLL_DOWN,
        },
        "decimal_urxvt": {
            "pattern": re.compile(r"(\d{1,2})\;(\d{1,3})\;(\d{1,3})()"),
            "32": MouseAction.LEFT_CLICK,
            "34": MouseAction.RIGHT_CLICK,
            "35": MouseAction.RELEASE,
            "64": MouseAction.LEFT_DRAG,
            "66": MouseAction.RIGHT_CLICK,
            "96": MouseAction.SCROLL_UP,
            "97": MouseAction.SCROLL_DOWN,
        },
    }

    mapping = mouse_codes[method]
    pattern = mapping["pattern"]

    events: list[MouseEvent | None] = []
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

                events.append(MouseEvent(action, (int(pos[0]), int(pos[1]))))
                continue

            events.append(None)

    return events


# shorthand functions
def print_to(pos: tuple[int, int], *args: Any, **kwargs: Any) -> None:
    """Print text to given `pos`.

    This passes through all arguments (except for `pos`) to the `print`
    method."""

    move_cursor(pos)
    print(*args, **kwargs, end="", flush=True)


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


def blink(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text blinking"""

    return set_mode("blink", False) + text + (reset() if reset_style else "")


def inverse(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text inverse-colored"""

    return set_mode("inverse", False) + text + (reset() if reset_style else "")


def invisible(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text as invisible

    Note: This isn't very widely supported"""

    return set_mode("invisible", False) + text + (reset() if reset_style else "")


def strikethrough(text: str, reset_style: Optional[bool] = True) -> str:
    """Return text as strikethrough"""

    return set_mode("strikethrough", False) + text + (reset() if reset_style else "")
