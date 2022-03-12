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

from typing import Optional, Any, Union, Callable, Tuple, Pattern
from dataclasses import dataclass, fields
from enum import Enum, auto as _auto
from sys import stdout as _stdout
from string import hexdigits
from os import name as _name, system
from shutil import get_terminal_size

from .input import getch

__all__ = [
    "Color",
    "foreground",
    "background",
    "terminal",
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


class Color:
    """Class to store various color utilities

    Shoutout to the best StackOverflow answer I've ever come across, that
    just so happens to be a great summary of ANSI color systems:
        https://stackoverflow.com/a/33206814

    Two instances of this class are provided, `foreground`
    and `background`. The difference between these is the color
    layer they operate on.

    To use this class you should call either instances with some
    data type representing a color. The following patterns are supported:

    - `int`: 0-256 terminal colors
    - `str`: Name of one of the registered named colors. See `Color.names`.
    - `#rrggbb`: RGB hex string. Note: alpha values are not supported.
    - `tuple[int, int]`: Tuple of RGB colors, each 0-256.

    When calling an instance of the class, the following args are set:

    Args:
        text: The string that will be colored.
        color: The color specifier.
        reset_color: A boolean that determines whether the returned value should
            end with a reset code. Defaults to True.

    Returns:
        The colored string.

    Raises:
        NotImplementedError: Unrecognized color specifier was passed.
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
        """Initialize Color object.

        Args:
            layer: One of [0, 1]. Objects instantiated with 0 will represent foreground
                colors, while objects instantiated with 1 will display background ones.

        Raises:
            NotImplementedError: Invalid layer.
        """

        if layer not in [0, 1]:
            raise NotImplementedError(f"Layer {layer} can only be one of [0, 1].")

        self.layer_offset = layer * 10

    @staticmethod
    def translate_hex(color: str) -> tuple[int, int, int]:
        """Translates a hex string of format #RRGGBB into an RGB tuple of integers.

        Args:
            color: The hexadecimal string to convert. Must follow the format #RRGGBB, where
                capitalization is optional.

        Returns:
            A tuple of integers, 0-255 each, standing for red, green and blue values in that
            order.
        """

        if color.startswith("#"):
            color = color[1:]

        rgb = []
        for i in (0, 2, 4):
            color_hex = color[i : i + 2]
            rgb.append(int(color_hex, 16))

        return rgb[0], rgb[1], rgb[2]

    def __call__(self, text: str, color: ColorType, reset_color: bool = True) -> str:
        """Colors a piece of text. See help(Color) for more info."""

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
"""`Color` instance for setting foreground colors."""

background = Color(1)
"""`Color` instance for setting background colors."""


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

    def fill(self, color: int = 0, flush: bool = True) -> None:
        """Fills the entire terminal with the given color.

        This is more of a debug function than anything, as performance is not the
        greatest.

        Args:
            color: An integer for the color to fill in. Must be in the 0-255 xterm
                color range.
            flush: Whether stdout should be flushed. Defaults to True, but setting
                it False can be beneficial for performance, as long as you flush in
                some other place.
        """

        for height in range(self.height):
            sys.stdout.write(
                f"\033[{height};0H"
                + background(" " * (self.width - 1), color)
                + ("\n" if flush else "")
            )


terminal = Terminal()
"""Terminal instance that should be used pretty much always."""

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

    _stdout.write(commands[what])


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

    _stdout.write("\x1b[s")


def restore_cursor() -> None:
    """Restore cursor position as saved by `save_cursor`."""

    _stdout.write("\x1b[u")


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
    _stdout.write(f"\x1b[{posy};{posx}H")


def cursor_up(num: int = 1) -> None:
    """Moves the cursor up by `num` lines.

    Args:
        num: How many lines the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_down`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}A")


def cursor_down(num: int = 1) -> None:
    """Moves the cursor up by `num` lines.

    Args:
        num: How many lines the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_up`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}B")


def cursor_right(num: int = 1) -> None:
    """Moves the cursor right by `num` lines.

    Args:
        num: How many characters the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_left`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}C")


def cursor_left(num: int = 1) -> None:
    """Moves the cursor left by `num` lines.

    Args:
        num: How many characters the cursor should move by. Must be positive,
            to move in the opposite direction use `cursor_right`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """Moves the cursor to the beginning of the `num`-th line downwards.

    Args:
        num: The amount the cursor should move by. Must be positive, to move
            in the opposite direction use `cursor_prev_line`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """Moves the cursor to the beginning of the `num`-th line upwards.

    Args:
        num: The amount the cursor should move by. Must be positive, to move
            in the opposite direction use `cursor_next_line`.
    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}F")


def cursor_column(num: int = 0) -> None:
    """Moves the cursor to the `num`-th character of the current line.

    Args:
        num: The new cursor position.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write(f"\x1b[{num}G")


def cursor_home() -> None:
    """Moves cursor to `terminal.origin`.

    Note:
        This does not flush the terminal for performance reasons. You
        can do it manually with `sys.stdout.flush()`.
    """

    _stdout.write("\x1b[H")


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
        _stdout.write(code)

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
    """Translates the output of produced by setting `report_mouse` into MouseEvents.

    This method currently only supports `decimal_xterm` and `decimal_urxvt`.

    Args:
        code: The string of mouse code(s) to translate.
        method: The reporting method to translate. One of [`decimal_xterm`, `decimal_urxvt`].

    Returns:
        A list of optional mouse events obtained from the code argument. If the code was malformed,
        and no codes could be determined None is returned.
    """

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
    """Resets printing mode.

    Args:
        reset_style: Boolean that determines whether a reset
            character should be appended to the end of the
            string.
    """

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
