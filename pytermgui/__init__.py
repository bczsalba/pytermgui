"""
pytermgui
---------
author: bczsalba


A simple and robust terminal UI library, written in Python.
"""

__version__ = "0.1.0"

from typing import Optional

from .input import getch, keys
from .helpers import Regex, strip_ansi, break_line
from .widgets import (
    Widget,
    Container,
    Label,
    ListView,
    Prompt,
    InputField,
    ProgressBar,
    ColorPicker,
)

from .context_managers import alt_buffer, cursor_at
from .ansi_interface import *
