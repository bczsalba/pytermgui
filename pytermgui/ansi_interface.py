"""
Various functions to interface with the terminal, using ANSI sequences.

Credits:
- https://wiki.bash-hackers.org/scripting/terminalcodes
- https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""

from __future__ import annotations

import asyncio
import re
import signal
import sys
from contextlib import contextmanager
from dataclasses import dataclass, fields
from enum import Enum, auto
from os import name
from shutil import get_terminal_size
from string import hexdigits
from types import FrameType
from typing import IO, Any, Callable, Literal, Optional, Union

from .input import getch

_IS_NT = name == "nt"
_SYS_HAS_FRAME = hasattr(sys, "_getframe")

if _IS_NT:
    import ctypes

    kernel32 = ctypes.windll.kernel32
else:
    import termios

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
    "overline",
]

_HEX_REGEX: re.Pattern = re.compile(r"#?[0-9a-zA-Z]{3,6}", re.IGNORECASE)
"""
Regex to validate HEX
"""

_CURSOR_POS_REGEX: re.Pattern = re.compile(r".*\x1b\[(?P<y>\d*);(?P<x>\d*)R")
"""
Regex to parse cursor query string
"""

DECORATION_MODES: dict[str, int] = {
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
"""
Dictionary of decoration modes
"""

MOUSE_EVENTS: dict[str, str] = {
    "press": "\x1b[?1000",
    "highlight": "\x1b[?1001",
    "press_hold": "\x1b[?1002",
    "hover": "\x1b[?1003",
}
"""
Dictionary of mouse events
"""

MOUSE_METHODS: dict[str, str] = {
    "decimal_utf8": "\x1b[?1005",
    "decimal_xterm": "\x1b[?1006",
    "decimal_urxvt": "\x1b[?1015",
}
"""
Dictionary of mouse methods
"""


class Color:
    """
    Class to store various color utilities

    Two instances of this class are provided, `foreground` and `background`. The difference between these is the color layer they operate on.

    To use this class you should call either instances with some data type representing a color. The following patterns are supported:

    - `int`: 0-256 terminal colors
    - `str`: Name of one of the registered named colors. See `Color.names`.
    - `#rrggbb` or '#rgb': RGB hex string. Note: alpha values are not supported.
    - `tuple[int, int]`: Tuple of RGB colors, each 0-256.
    """

    ColorType = Union[int, str, tuple[int, int, int]]
    """
    A simple type to represent color patterns. See `Color` for more info
    """

    names: dict[str, int] = {
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
    """
    16 default named colors.

    Expanding this list will expand the names `pytermgui.parser.markup` will recognize, but if that is your objective it is better to use `pytermgui.parser.MarkupLanguage.alias`.
    """

    def __init__(self, layer: Literal[0, 1] = 0) -> None:
        """Initialize object

        `layer` can be either 0 or 1. This value determines whether the instance will represent foreground or background colors.
        """

        if layer not in (0, 1):
            raise NotImplementedError(f"Layer {layer} can only be one of (0, 1).")

        self.layer_offset = layer * 10

    @staticmethod
    def translate_hex(color: str) -> tuple[int, int, int]:
        """
        Translate hex string of format '#RGB' or '#RRGGBB' into an 'RGB' tuple of integers
        """

        if not _HEX_REGEX.match(color):
            raise ValueError(f"{color} should be in '#RGB' or '#RRGGBB' format")

        if color.startswith("#"):
            color = color[1:]

        if len(color) == 3:
            color = "".join(part * 2 for part in color)

        rgb = int(color, 16)

        return ((rgb & 0xFF0000) >> 16, (rgb & 0x00FF00) >> 8, (rgb & 0x0000FF))

    def __call__(self, text: str, color: ColorType, reset_color: bool = True) -> str:
        """
        Color a piece of text using `color`.

        The color can be one of 4 formats:
            - str colorname:   One of the predifined named colors. See the names dict.
            - int 0-256:       One of the 256 terminal colors.
            - str #RRGGBB:     CSS-style HEX string, without alpha.
            - tuple (0-256, 0-256, 0-256): Tuple of integers, representing an RGB color.

        If `reset_color` is set a reset sequence is inserted at the end.
        """

        if isinstance(color, str):
            try:
                color = self.translate_hex(color)
            except ValueError:
                # value is not a hex number, but is string
                pass

        if color in self.names:
            color = self.names.get(color, color)

        # 24-bit/RGB values (16581375 ≈16m colors)
        if isinstance(color, tuple) and all([isinstance(part, int) for part in color]):
            red, green, blue = color
            color_value = f"2;{red};{green};{blue}m"
        # 8-bit/Xterm colors (256 colors)
        elif int(color) in range(256):
            color_value = f"5;{color}m"
        else:
            raise NotImplementedError(
                f"Not sure what to do with {color} of type {type(color)}"
            )
        ending = "\x1b[0m" if reset_style else ""
        return f"\x1b[{38 + self.layer_offset};{color_value}{text}{ending}"


foreground: Color = Color(0)
"""
`Color` instance to setting foreground colors
"""

background: Color = Color(1)
"""
`Color` instance to setting background colors
"""


class TerminalModes:
    """
    A class to change terminal modes
    """

    def __init__(self) -> None:
        """
        Initialize `TerminalModes` class
        """
        if _IS_NT:
            self._OldStdinMode = ctypes.wintypes.DWORD()
            self._OldStdoutMode = ctypes.wintypes.DWORD()
            kernel32.GetConsoleMode(
                kernel32.GetStdHandle(-10), ctypes.byref(self._OldStdinMode)
            )
            kernel32.GetConsoleMode(
                kernel32.GetStdHandle(-11), ctypes.byref(self._OldStdoutMode)
            )
        else:
            self._OldStdinMode = termios.tcgetattr(sys.stdin)

    @contextmanager
    def NoEcho(self) -> None:
        if _IS_NT:
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 0)
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        else:
            _ = self._OldStdinMode
            _[3] = _[3] & ~(termios.ECHO | termios.ICANON)
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, _)
        try:
            yield
        finally:
            if _IS_NT:
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), self._OldStdinMode)
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), self._OldStdoutMode)
            else:
                termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, self._OldStdinMode)


terminal_modes = TerminalModes()
"""
TerminalModes instance
"""


class Terminal:
    """
    A class to store & access data about a terminal
    """

    RESIZE = 0
    margins = [0, 0, 0, 0]

    def __init__(self) -> None:
        """
        Initialize 'Terminal' class
        """
        self.origin: tuple[int, int] = (1, 1)
        self.size: tuple[int, int] = get_terminal_size()
        self._listeners: dict[int, list[Callable[..., Any]]] = {}
        # TODO: Windows doesn't support SIGWINCH, is there another alternative?
        if _IS_NT:
            asyncio.run(self._WinSIGWINCH())
        else:
            signal.signal(signal.SIGWINCH, self._update_size)

    async def _WinSIGWINCH(self) -> None:
        while True:
            n_width = get_terminal_size()
            if n_width != self.size:
                self._update_size(28, (sys._getframe(1) if _SYS_HAS_FRAME else None))
            await asyncio.sleep(0.5)

    def _call_listener(self, event: int, data: Any) -> None:
        """
        Call event callback is one is found.
        """
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(data)

    def _update_size(self, signum: int, frame: FrameType) -> None:
        """
        Resize terminal when SIGWINCH or _WinSIGWINCH occurs
        """
        self.size = get_terminal_size()
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
        """
        Subscribe a callback function to an event

        The callback takes an event-specific argument payload:
            RESIZE: tuple[int, int] - New screen size
        """
        if not event in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def fill(self, color: int = 0, flush: bool = True) -> None:
        """
        Fill entire terminal with a color
        """
        _fill = background(" " * (self.width - 1), color)
        for height in range(self.height):
            sys.stdout.write(f"\x1b[{height};0H{fill}")
        if flush:
            sys.stdout.flush()


terminal = Terminal()
"""
Terminal instance
"""


def is_interactive() -> bool:
    """
    Determine whether shell is interactive.

    A shell is interactive if it is run from `python3` or `python3 -i`
    """
    return hasattr(sys, "ps1")


# screen commands
def save_screen() -> None:
    """
    Sets screen to alternative state ("cup" mode)

    Use `unset_alt_screen()` to restore screen state
    """
    sys.stdout.write("\x1b[?47h")


def restore_screen() -> None:
    """
    Restore screen state
    """
    sys.stdout.write("\x1b[?47l")


def set_alt_buffer() -> None:
    """
    Start alternate buffer

    Note: This buffer is unscrollable
    """
    sys.stdout.write("\x1b[?1049h")


def unset_alt_buffer() -> None:
    """
    Return to main buffer from alt, restoring its original state
    """
    sys.stdout.write("\x1b[?1049l")


def clear(what: str = "screen") -> None:
    """
    Clear specified region

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

    sys.stdout.write(commands.get(what, ""))


# cursor commands
def hide_cursor() -> None:
    """
    Stop printing cursor
    """
    sys.stdout.write("\x1b[?25l")


def show_cursor() -> None:
    """
    Start printing cursor
    """
    sys.stdout.write("\x1b[?25h")


def save_cursor() -> None:
    """
    Save cursor position.

    Use `restore_cursor()` to restore it.
    """
    sys.stdout.write("\x1b[s")


def restore_cursor() -> None:
    """
    Restore cursor position saved by `save_cursor()`
    """
    sys.stdout.write("\x1b[u")


def report_cursor() -> Optional[tuple[int, int]]:
    """
    Get position of cursor
    """
    if _IS_NT:
        OldStdinMode = ctypes.wintypes.DWORD()
        OldStdoutMode = ctypes.wintypes.DWORD()
        kernel32.GetConsoleMode(kernel32.GetStdHandle(-10), ctypes.byref(OldStdinMode))
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 0)
        kernel32.GetConsoleMode(kernel32.GetStdHandle(-11), ctypes.byref(OldStdoutMode))
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    else:
        _ = OldStdinMode = termios.tcgetattr(sys.stdin)
        _[3] = _[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, _)
    try:
        _ = ""
        sys.stdout.write("\x1b[6n")
        sys.stdout.flush()
        while not _.endswith("R"):
            _ += sys.stdin.read(1)
        res = _CURSOR_POS_REGEX.match(_)
    finally:
        if _IS_NT:
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), OldStdinMode)
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), OldStdoutMode)
        else:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, OldStdinMode)
    if res:  # if match is found
        return (int(res.group("x")), int(res.group("y")))
    # Even without `return None` it returns `None` by default


def move_cursor(pos: tuple[int, int]) -> None:
    """
    Move cursor to `pos`.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{pos[1]};{pos[0]}H")


def cursor_up(num: int = 1) -> None:
    """
    Move cursor up by `num` lines.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}A")


def cursor_down(num: int = 1) -> None:
    """
    Move cursor down by `num` lines.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}B")


def cursor_right(num: int = 1) -> None:
    """
    Move cursor left by `num` cols.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}C")


def cursor_left(num: int = 1) -> None:
    """
    Move cursor left by `num` cols.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """
    Move cursor to beginning of `num`-th line down.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """
    Move cursor to beginning of `num`-th line down.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}F")


def cursor_column(num: int = 0) -> None:
    """
    Move cursor to `num`-th column in the current line.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write(f"\x1b[{num}G")


def cursor_home() -> None:
    """
    Move cursor to `terminal.origin`.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """
    sys.stdout.write("\x1b[H")


def set_mode(mode: Union[str, int], write: bool = True) -> str:
    """
    Set text decoration mode

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
    - 53 - `overline`

    You can use both the digit and text forms, though you should really be
    using one of the specific setters, like `bold` or `italic`.
    """
    if isinstance(mode, str) and (not mode.isdigit()):
        mode = DECORATION_MODES.get(mode, None)
    if isinstance(mode, int) and mode in options.values():
        if write:
            sys.stdout.write(f"\x1b[{mode}m")
        return f"\x1b[{mode}m"
    return ""


def set_echo() -> None:
    """
    Start echoing user input
    """
    if _IS_NT:
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 0)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    else:
        _ = terminal_modes._OldStdinMode
        _[3] = _[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, _)


def unset_echo() -> None:
    """
    Stop echoing user input
    """
    if _IS_NT:
        kernel32.SetConsoleMode(
            kernel32.GetStdHandle(-10), terminal_modes._OldStdinMode
        )
        kernel32.SetConsoleMode(
            kernel32.GetStdHandle(-11), terminal_modes._OldStdoutMode
        )
    else:
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, terminal_modes._OldStdinMode)


class MouseAction(Enum):
    """
    An enumeration of all the polled mouse actions
    """

    LEFT_CLICK = auto()
    """
    Start of a left button action sequence
    """
    LEFT_DRAG = auto()
    """
    Mouse moved while left button was held down
    """
    RIGHT_CLICK = auto()
    """
    Start of a right button action sequence
    """
    RIGHT_DRAG = auto()
    """
    Mouse moved while right button was held down
    """
    SCROLL_UP = auto()
    """
    Mouse wheel or touchpad scroll upwards
    """
    SCROLL_DOWN = auto()
    """
    Mouse wheel or touchpad scroll downwards
    """
    HOVER = auto()
    """
    Mouse moved without clicking

    Note: This only gets registered when hover events are listened to
    """
    RELEASE = auto()
    """
    Mouse button released; end of any and all mouse action sequences
    """


@dataclass
class MouseEvent:
    """
    A class to represent events created by mouse actions.

    Its first argument is a `MouseAction` describing what happened, and its second argument is a `tuple[int, int]` describing where it happened.

    This class mostly exists for readability & typing reasons. It also implements the iterable protocol, so you can use the unpacking syntax, such as:

    ```python3
    action, position = MouseEvent(...)
    ```
    """

    action: MouseAction
    position: tuple[int, int]

    def __post_init__(self) -> None:
        """
        Initialize iteration counter
        """
        self._iter_index = 0

    def __next__(self) -> Union[MouseAction, tuple[int, int]]:
        """
        Get next iteration item
        """
        data = fields(self)

        if self._iter_index >= len(data):
            self._iter_index = 0
            raise StopIteration

        self._iter_index += 1
        return getattr(self, data[self._iter_index - 1].name)

    def __iter__(self) -> MouseEvent:
        """
        Start iteration
        """
        return self


mouse_codes: dict[str, object] = {
    "decimal_utf8": {
        "pattern": re.compile(
            r"\x1b\[M(?P<EventType>(0|2|3[245]|6[45]))\;(?P<X>\d+)\;(?P<Y>\d+)"
        ),
        ### TODO ###
    },
    "decimal_xterm": {
        "pattern": re.compile(
            r"\x1b\[\<(?P<EventType>(0|2|3[245]|6[45]))\;(?P<X>\d+)\;(?P<Y>\d+)(?P<ID>[mM])"
        ),
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
        "pattern": re.compile(
            r"\x1b\[(?P<EventType>(0|2|3[245]|6[45]))\;(?P<X>\d+)\;(?P<Y>\d+)M"
        ),
        "32": MouseAction.LEFT_CLICK,
        "34": MouseAction.RIGHT_CLICK,
        "35": MouseAction.RELEASE,
        "64": MouseAction.LEFT_DRAG,
        "66": MouseAction.RIGHT_DRAG,
        "96": MouseAction.SCROLL_UP,
        "97": MouseAction.SCROLL_DOWN,
    },
}


def report_mouse(
    event: str, method: Optional[str] = "decimal_xterm", stop: bool = False
) -> None:
    """
    Start reporting mouse events.

    Options:
    - `press`
    - `highlight`
    - `press_hold`
    - `hover`

    Methods:
    - `None`: Limited in coordinates, not recommended.
    - `decimal_xterm`: Default, most universal
    - `decimal_urxvt`: Older, less compatible
    - `decimal_utf8`:  Apparently not too stable

    More information <a href='https://stackoverflow.com/a/5970472'>here</a>.

    Note:
        If you need this functionality, you're probably better off using the wrapper `pytermgui.context_managers.mouse_handler`, which allows listening on multiple events, gives a translator method and handles exceptions.
    """
    _ending = "l" if stop else "h"
    _event = MOUSE_EVENTS.get(event, None)
    _method = MOUSE_METHODS.get(method, None)
    if _event:
        return f"{_event}{_ending}"
    else:
        raise NotImplementedError(f"Mouse report event {event} is not supported!")
    if method is None:
        return
    elif _method:
        return f"{_method}{_ending}"
    else:
        raise NotImplementedError(f"Mouse report method {method} is not supported!")


def translate_mouse(code: str, method: str) -> Optional[list[Optional[MouseEvent]]]:
    """
    Translate the output of produced by setting report_mouse codes into MouseEvent-s.

    This currently only supports `decimal_xterm` and `decimal_urvxt`. `decimal_utf8` is currently WIP. See `report_mouse` for more information.
    """
    mapping = mouse_codes.get(method, None)
    pattern = mapping["pattern"]
    events: list[Optional[MouseEvent]] = []
    for match in pattern.finditer(code):
        if method == "decimal_xterm":
            identifier = match.group("ID")
        else:
            identifier = ""
        action: string = f"{match.group('EventType')}{identifier}"
        pos_x: int = int(match.group("X"))
        pos_y: int = int(match.group("Y"))
        events.append(MouseEvent(action, (pos_x, pos_y)))
    return events


# shorthand functions
def print_to(
    pos: tuple[int, int],
    *objects: Any,
    sep: str = " ",
    end: str = " ",
    file: Optional[IO[str]] = None,
    flush: bool = True,
) -> None:
    """
    Print text to given `pos`.

    This passes through all arguments (except for `pos`) to the `print` method.
    """
    move_cursor(pos)
    print(*objects, sep=sep, end=end, file=file, flush=flush)


def reset() -> str:
    """
    Reset printing mode
    """
    return "\x1b[0m"


def bold(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text in bold
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[1m{text}{ending}"


def dim(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text in dim
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[2m{text}{ending}"


def italic(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text in italic
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[3m{text}{ending}"


def underline(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text underlined
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[4m{text}{ending}"


def blink(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text blinking
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[5m{text}{ending}"


def inverse(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text inverse-colored
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[7m{text}{ending}"


def invisible(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text as invisible

    Note: This isn't very widely supported
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[8m{text}{ending}"


def strikethrough(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text as strikethrough
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[9m{text}{ending}"


def overline(text: str, reset_style: Optional[bool] = True) -> str:
    """
    Return text overlined

    Note: This isnt' very widely supported
    """
    ending = "\x1b[0m" if reset_style else ""
    return f"\x1b[53m{text}{ending}"
