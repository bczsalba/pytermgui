"""
pytermgui.input
---------------
author: bczsalba


File providing the getch() function to easily read character inputs.

credits:
    - original getch implementation: Danny Yoo (https://code.activestate.com/recipes/134892)
    - modern additions & idea:       kcsaff (https://github.com/kcsaff/getkey)
"""

# pylint doesn't see the C source
# pylint: disable=c-extension-no-member, no-name-in-module

import os
import sys
from typing import IO, AnyStr, Generator, Any
from select import select
from codecs import getincrementaldecoder

try:
    import tty
    import termios
except ImportError:
    # we're running windows
    pass


def _is_ready(file: IO[AnyStr]) -> bool:
    """Return if file is reading for reading"""

    result = select([file], [], [], 0.0)
    return len(result[0]) > 0


class _GetchUnix:
    """Getch implementation for UNIX"""

    def __init__(self) -> None:
        """Set up instance attributes"""

        self.decode = getincrementaldecoder(sys.stdin.encoding)().decode

    def _read(self, num: int) -> str:
        """Read num characters from sys.stdin"""

        buff = ""
        while len(buff) < num:
            char = os.read(sys.stdin.fileno(), 1)
            try:
                buff += self.decode(char)
            except UnicodeDecodeError:
                buff += str(char)

        return buff

    def get_chars(self) -> Generator[str, None, None]:
        """Get characters while possible, yield them"""

        descriptor = sys.stdin.fileno()
        old_settings = termios.tcgetattr(descriptor)
        tty.setcbreak(descriptor)

        try:
            yield self._read(1)

            while _is_ready(sys.stdin):
                yield self._read(1)

        finally:
            # reset terminal state, set echo on
            termios.tcsetattr(descriptor, termios.TCSADRAIN, old_settings)

    def __call__(self) -> str:
        """Return all characters that can be read"""

        buff = "".join(self.get_chars())
        return buff


# running on Windows
try:
    import msvcrt

    _platform_keys = {
        "name": "nt",
        "ESC": "\x1b",
        "LEFT": "\xe0K",
        "RIGHT": "\xe0M",
        "UP": "\xe0H",
        "DOWN": "\xe0P",
        "ENTER": "\r",
        "BACKSPACE": "\x08",
    }

    _getch = msvcrt.wgetch  # type: ignore

# running on POSIX
except ImportError:
    _platform_keys = {
        "name": "posix",
        "UP": "\033[A",
        "DOWN": "\033[B",
        "LEFT": "\033[C",
        "RIGHT": "\033[D",
        "BACKSPACE": "\x7f",
        "INSERT": "\x1b[2~",
        "DELETE": "\x1b[3~",
    }

    _getch = _GetchUnix()


def getch(printable: bool = False) -> Any:
    """Wrapper for the getch functions"""

    key = _getch()

    if printable:
        key = key.encode("unicode_escape").decode("utf-8")

    return key
