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
# pylint: disable=too-few-public-methods, arguments-differ


from typing import Optional, Any, Union
from subprocess import run, Popen
from sys import stdout

from .input import getch


class _Color:
    """Parent class for Color objects"""

    def __init__(self, layer: int = 0) -> None:
        """Set layer"""

        if layer not in [0, 1]:
            raise NotImplementedError(
                f"Layer {layer} is not supported for Color256 objects! Please choose from 0, 1"
            )

        self.layer_offset = layer * 10

    def __call__(
        self,
        text: str,
        color: Union[
            int, str, tuple[Union[int, str], Union[int, str], Union[int, str]]
        ],
    ) -> str:
        """Return colored text with reset code at the end"""

        if not isinstance(color, tuple):
            color = str(color)

        color_value = self.get_color(color)
        if color_value is None:
            return text

        return color_value + text + set_mode("reset")

    def get_color(self, attr: Any) -> Optional[str]:
        """This method needs to be overwritten."""

        _ = self
        return str(attr)


class Color16(_Color):
    """Class for using 16-bit colors"""

    def __init__(self, layer: int = 0) -> None:
        """Set up _colors dict"""

        super().__init__(layer)

        self._colors = {
            "black": 30,
            "red": 31,
            "green": 32,
            "yellow": 33,
            "blue": 34,
            "magenta": 35,
            "cyan": 36,
            "white": 37,
        }

    def __getattr__(self, attr: str) -> Optional[str]:
        return self.get_color(attr)

    def get_color(self, attr: str) -> Optional[str]:
        """Overwrite __getattr__ to look in self._colors"""

        if str(attr).isdigit():
            if not 30 <= int(attr) <= 37:
                return None

            color = int(attr)

        else:
            color = self._colors[attr]

        return f"\033[{color+(self.layer_offset)}m"


class Color256(_Color):
    """Class for using 256-bit colors"""

    def get_color(self, attr: str) -> Optional[str]:
        """Return color values"""

        if not attr.isdigit():
            return None

        if not 1 <= int(attr) <= 255:
            return None

        return f"\033[{38+self.layer_offset};5;{attr}m"


class ColorRGB(_Color):
    """Class for using RGB or HEX colors

    Note:
        This requires a true-color terminal, like Kitty or Alacritty."""

    @staticmethod
    def _translate_hex(color: str) -> tuple[int, int, int]:
        """Translate hex string to rgb values"""

        if color.startswith("#"):
            color = color[1:]

        rgb = []
        for i in (0, 2, 4):
            rgb.append(int(color[i : i + 2], 16))

        return rgb[0], rgb[1], rgb[2]

    def get_color(self, colors: Union[str, tuple[int, int, int]]) -> Optional[str]:
        """Get RGB color code"""

        if isinstance(colors, str):
            colors = self._translate_hex(colors)

        if not len(colors) == 3:
            return None

        for col in colors:
            if not str(col).isdigit():
                return None

        strings = [str(col) for col in colors]
        return f"\033[{38+self.layer_offset};2;" + ";".join(strings) + "m"


# helpers
def tput(command: list[str]) -> None:
    """Shorthand for tput calls"""

    waited_commands = [
        "clear",
        "smcup",
        "cup",
    ]

    command.insert(0, "tput")
    str_command = [str(c) for c in command]

    if command[1] in waited_commands:
        run(str_command, check=True)
        return

    Popen(str_command)


# screen commands
def get_screen_size() -> Optional[tuple[int, int]]:
    """Get screen size by moving to an impossible location
    and getting new cursor position"""

    save_cursor()
    move_cursor((9999, 9999))
    size = report_cursor()
    restore_cursor()

    return size


def width() -> int:
    """Get screen width"""

    size = get_screen_size()

    if size is None:
        return 0
    return size[0]


def height() -> int:
    """Get screen height"""

    size = get_screen_size()

    if size is None:
        return 0
    return size[1]


def save_screen() -> None:
    """Save the contents of the screen, wipe.
    Use `restore_screen()` to get them back."""

    # print("\033[?47h")
    tput(["smcup"])


def restore_screen() -> None:
    """Restore the contents of the screen,
    previously saved by a call to `save_screen()`."""

    # print("\033[?47l")
    tput(["rmcup"])


def start_alt_buffer() -> None:
    """Start alternate buffer that is non-scrollable"""

    print("\033[?1049h")


def end_alt_buffer() -> None:
    """Return to main buffer from alt, restoring state"""

    print("\033[?1049l")


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
        "eos": "\033[0J",
        "bos": "\033[1J",
        "screen": "\033[2J",
        "eol": "\033[0K",
        "bol": "\033[1K",
        "line": "\033[2K",
    }

    stdout.write(commands[what])


# cursor commands
def hide_cursor() -> None:
    """Don't print cursor"""

    # tput(['civis'])
    print("\033[?25l")


def show_cursor() -> None:
    """Set cursor printing back on"""

    # tput(['cvvis'])
    print("\033[?25h")


def save_cursor() -> None:
    """Save cursor position, use `restore_cursor()`
    to restore it."""

    # tput(['sc'])
    stdout.write("\033[s")


def restore_cursor() -> None:
    """Restore cursor position saved by `save_cursor()`"""

    # tput(['rc'])
    stdout.write("\033[u")


def report_cursor() -> Optional[tuple[int, int]]:
    """Get position of cursor"""

    print("\033[6n")
    chars = getch()
    posy, posx = chars[2:-1].split(";")

    if not posx.isdigit() or not posy.isdigit():
        return None

    return int(posx), int(posy)


def move_cursor(pos: tuple[int, int]) -> None:
    """Move cursor to pos"""

    posx, posy = pos
    stdout.write(f"\033[{posy};{posx}H")


def cursor_up(num: int = 1) -> None:
    """Move cursor up by `num` lines"""

    stdout.write(f"\033[{num}A")


def cursor_down(num: int = 1) -> None:
    """Move cursor down by `num` lines"""

    stdout.write(f"\033[{num}B")


def cursor_right(num: int = 1) -> None:
    """Move cursor left by `num` cols"""

    stdout.write(f"\033[{num}C")


def cursor_left(num: int = 1) -> None:
    """Move cursor left by `num` cols"""

    stdout.write(f"\033[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """Move cursor to beginning of num-th line down"""

    stdout.write(f"\033[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """Move cursor to beginning of num-th line down"""

    stdout.write(f"\033[{num}F")


def cursor_column(num: int = 0) -> None:
    """Move cursor to num-th column in the current line"""

    stdout.write(f"\033[{num}G")


def cursor_home() -> None:
    """Move cursor to HOME"""

    stdout.write("\033[H")


def set_mode(mode: Union[str, int]) -> str:
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

    code = f"\033[{mode}m"
    stdout.write(code)

    return code


# shorthand functions
def print_to(pos: tuple[int, int], *args: tuple[Any, ...]) -> None:
    """Print text to given position"""

    text = ""
    for arg in args:
        text += " " + str(arg)

    move_cursor(pos)
    print(text)
