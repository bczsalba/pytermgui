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

Todo:
    - 16-color palette
    - 256-color palette
        + 38;5 - fg
        + 48;5 - bg
    - rgb palette
        + 38;5 - fg
        + 48;5 - bg
    - \033[{0-9}m

Credits:
    - https://wiki.bash-hackers.org/scripting/terminalcodes
    - https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""

from subprocess import run, Popen
from typing import Optional, Any
from sys import stdout
from .input import getch


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


# shorthand functions
def print_to(pos: tuple[int, int], *args: tuple[Any, ...]) -> None:
    """Print text to given position"""

    text = ""
    for arg in args:
        text += " " + str(arg)

    move_cursor(pos)
    print(text)
