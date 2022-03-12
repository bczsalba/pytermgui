"""
File providing the getch() function to easily read character inputs.

Credits:
- Original getch implementation: Danny Yoo (https://code.activestate.com/recipes/134892)
- Modern additions & idea:       kcsaff (https://github.com/kcsaff/getkey)
"""

# pylint doesn't see the C source
# pylint: disable=c-extension-no-member, no-name-in-module

from __future__ import annotations

import os
import sys

from typing import (
    IO,
    Any,
    Union,
    AnyStr,
    Optional,
    KeysView,
    Generator,
    ItemsView,
    ValuesView,
)

from select import select
from codecs import getincrementaldecoder

__all__ = ["Keys", "getch", "keys"]


def _is_ready(file: IO[AnyStr]) -> bool:
    """Determines if IO object is reading to read.

    Args:
        file: An IO object of any type.

    Returns:
        A boolean describing whether the object has unread
        content.
    """

    result = select([file], [], [], 0.0)
    return len(result[0]) > 0


class _GetchUnix:
    """Getch implementation for UNIX systems."""

    def __init__(self) -> None:
        """Initializes object."""

        if sys.stdin.encoding is not None:
            self.decode = getincrementaldecoder(sys.stdin.encoding)().decode
        else:
            self.decode = lambda item: item

    def _read(self, num: int) -> str:
        """Reads characters from sys.stdin.

        Args:
            num: How many characters should be read.

        Returns:
            The characters read.
        """

        buff = ""
        while len(buff) < num:
            char = os.read(sys.stdin.fileno(), 1)
            try:
                buff += self.decode(char)
            except UnicodeDecodeError:
                buff += str(char)

        return buff

    def get_chars(self) -> Generator[str, None, None]:
        """Yields characters while there are some available.

        Yields:
            Any available characters.
        """

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
        """Returns all characters that can be read."""

        buff = "".join(self.get_chars())
        return buff


class _GetchWindows:
    """Getch implementation for Windows."""

    @staticmethod
    def _ensure_str(string: AnyStr) -> str:
        """Ensures return value is always a `str` and not `bytes`.

        Args:
            string: Any string or bytes object.

        Returns:
            The string argument, converted to `str`.
        """

        if isinstance(string, bytes):
            return string.decode("utf-8")

        return string

    def get_chars(self) -> str:
        """Reads characters from sys.stdin.

        Returns:
            All read characters.
        """

        # We need to type: ignore these on non-windows machines,
        # as the library does not exist.

        # Return empty string if there is no input to get
        if not msvcrt.kbhit():  # type: ignore
            return ""

        char = msvcrt.getch()  # type: ignore
        if char == b"\xe0":
            char = "\x1b"

        buff = self._ensure_str(char)

        while msvcrt.kbhit():  # type: ignore
            char = msvcrt.getch()  # type: ignore
            buff += self._ensure_str(char)

        return buff

    def __call__(self) -> str:
        """Returns all characters that can be read.

        Returns:
            All readable characters.
        """

        buff = self.get_chars()
        return buff


class Keys:
    """Class for easy access to key-codes.

    The keys for CTRL_{ascii_letter}-s can be generated with
    the following code:

    ```python3
    for i, letter in enumerate(ascii_lowercase):
        key = f"CTRL_{letter.upper()}"
        code = chr(i+1).encode('unicode_escape').decode('utf-8')

        print(key, code)
    ```
    """

    def __init__(self, platform_keys: dict[str, str], platform: str) -> None:
        """Initialize Keys object.

        Args:
            platform_keys: A dictionary of platform-specific keys.
            platform: The platform the program is running on.
        """

        self._keys = {
            "SPACE": " ",
            "ESC": "\x1b",
            # The ALT character in key combinations is the same as ESC
            "ALT": "\x1b",
            "TAB": "\t",
            "ENTER": "\n",
            "RETURN": "\n",
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
        }

        self.platform = platform

        if platform_keys is not None:
            for key, code in platform_keys.items():
                if key == "name":
                    self.name = code
                    continue

                self._keys[key] = code

    def __getattr__(self, attr: str) -> str:
        """Gets attr from self._keys."""

        if attr == "ANY_KEY":
            return attr

        return self._keys.get(attr, "")

    def get_name(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Gets canonical name of a key code.

        Args:
            key: The key to get the name of.
            default: The return value to substitute if no canonical name could be
                found. Defaults to None.

        Returns:
            The canonical name if one can be found, default otherwise.
        """

        for name, value in self._keys.items():
            if key == value:
                return name

        return default

    def values(self) -> ValuesView[str]:
        """Returns values() of self._keys."""

        return self._keys.values()

    def keys(self) -> KeysView[str]:
        """Returns keys() of self._keys."""

        return self._keys.keys()

    def items(self) -> ItemsView[str, str]:
        """Returns items() of self._keys."""

        return self._keys.items()


_getch: Union[_GetchWindows, _GetchUnix]

keys: Keys
"""Instance storing platform specific key codes."""

try:
    import msvcrt

    # TODO: Add shift+arrow keys
    _platform_keys = {
        "ESC": "\x1b",
        "LEFT": "\x1bK",
        "RIGHT": "\x1bM",
        "UP": "\x1bH",
        "DOWN": "\x1bP",
        "ENTER": "\r",
        "RETURN": "\r",
        "BACKSPACE": "\x08",
    }

    _getch = _GetchWindows()
    keys = Keys(_platform_keys, "nt")

except ImportError as import_error:
    if not os.name == "posix":
        raise NotImplementedError(
            f"Platform {os.name} is not supported."
        ) from import_error

    import termios
    import tty

    _platform_keys = {
        "name": "posix",
        "UP": "\x1b[A",
        "DOWN": "\x1b[B",
        "RIGHT": "\x1b[C",
        "LEFT": "\x1b[D",
        "SHIFT_UP": "\x1b[1;2A",
        "SHIFT_DOWN": "\x1b[1;2B",
        "SHIFT_RIGHT": "\x1b[1;2C",
        "SHIFT_LEFT": "\x1b[1;2D",
        "BACKSPACE": "\x7f",
        "INSERT": "\x1b[2~",
        "DELETE": "\x1b[3~",
        "BACKTAB": "\x1b[Z",
    }

    _getch = _GetchUnix()
    keys = Keys(_platform_keys, "posix")


def getch(printable: bool = False, interrupts: bool = True) -> Any:
    """Wrapper to call the platform-appropriate character getter.

    Args:
        printable: When set, printable versions of the input are returned.
        interrupts: If not set, `KeyboardInterrupt` is silenced and `chr(3)`
            (`CTRL_C`) is returned.
    """

    try:
        key = _getch()

        # msvcrt.getch returns CTRL_C as a character, unlike UNIX systems
        # where an interrupt is raised. Thus, we need to manually raise
        # the interrupt.
        if key == chr(3):
            raise KeyboardInterrupt

    except KeyboardInterrupt as error:
        if interrupts:
            raise KeyboardInterrupt("Unhandled interrupt") from error

        key = chr(3)

    if printable:
        key = key.encode("unicode_escape").decode("utf-8")

    return key
