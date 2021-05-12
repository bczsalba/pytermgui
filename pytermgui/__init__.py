"""
pytermgui
---------
author: bczsalba


A simple and robust terminal UI library, written in Python.
"""

__version__ = "0.1.0"

from typing import Optional

from .input import getch, _platform_keys
from .helpers import Regex, strip_ansi, break_line
from .classes import BaseElement, Container, Label, ListView, Prompt
from .context_managers import alt_buffer, cursor_at

from .ansi_interface import *

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

    def __getattr__(self, key: str) -> Optional[str]:
        """Overwrite __getattr__ to look in self._keys"""

        return self._keys[key]

    def __repr__(self) -> str:
        """Stringify object"""

        return f"Keys(platform={self.name})"

keys = _Keys(_platform_keys)
