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
import tty
import sys
import termios

from typing import (
    IO,
    AnyStr,
    Generator,
    Any,
    Optional,
    ValuesView,
    KeysView,
    ItemsView,
)

from select import select
from codecs import getincrementaldecoder


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


class _Keys:
    """Class for easy access to key-codes

    The keys for CTRL_{ascii_letter}-s can be generated with
    the following code:

    ```
    for i, letter in enumerate(ascii_lowercase):
        key = f"CTRL_{letter.upper()}"
        code = chr(i+1).encode('unicode_escape').decode('utf-8')

        print(key, code)
    ```
    """

    def __init__(self, platform_keys: Optional[dict[str, str]] = None) -> None:
        """Set up key values"""

        self._keys = {
            "CTRL_A": "\x01",
            "CTRL_B": "\x02",
            "CTRL_C": "\x03",
            "CTRL_D": "\x04",
            "CTRL_E": "\x05",
            "CTRL_F": "\x06",
            "CTRL_G": "\x07",
            "CTRL_H": "\x08",
            "CTRL_I": "\t",
            "CTRL_J": "\n",
            "CTRL_K": "\x0b",
            "CTRL_L": "\x0c",
            "CTRL_M": "\r",
            "CTRL_N": "\x0e",
            "CTRL_O": "\x0f",
            "CTRL_P": "\x10",
            "CTRL_Q": "\x11",
            "CTRL_R": "\x12",
            "CTRL_S": "\x13",
            "CTRL_T": "\x14",
            "CTRL_U": "\x15",
            "CTRL_V": "\x16",
            "CTRL_W": "\x17",
            "CTRL_X": "\x18",
            "CTRL_Y": "\x19",
            "CTRL_Z": "\x1a",
            "SPACE": " ",
            "ESC": "\x1b",
            "ENTER": "\n",
            "RETURN": "\n",
        }

        self.name = "Unknown"

        if platform_keys is not None:
            for key, code in platform_keys.items():
                if key == "name":
                    self.name = code
                    continue

                self._keys[key] = code

    def __getattr__(self, attr: str) -> str:
        """Overwrite __getattr__ to get from self._keys"""

        return self._keys[attr]

    def values(self) -> ValuesView[str]:
        """Return values() of self._keys"""

        return self._keys.values()

    def keys(self) -> KeysView[str]:
        """Return keys() of self._keys"""

        return self._keys.keys()

    def items(self) -> ItemsView[str, str]:
        """Return items() of self._keys"""

        return self._keys.items()

    def __repr__(self) -> str:
        """Stringify object"""

        return f"Keys(platform={self.name})"


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


keys = _Keys(_platform_keys)
