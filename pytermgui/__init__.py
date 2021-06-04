"""
pytermgui
---------
author: bczsalba


A simple and robust terminal UI library, written in Python.
"""

from .ansi_interface import __all__ as _ansi_all
from .serializer import __all__ as _serializer_all
from .widgets import __all__ as _widgets_all
from .parser import __all__ as _parser_all

__all__ = [
    "__version__",
    "getch",
    "keys",
    "strip_ansi",
    "break_line",
    "real_length",
    "alt_buffer",
    "cursor_at",
    "cursor_up",
    "Widget",
    "Container",
    "Label",
    "ListView",
    "Prompt",
    "InputField",
    "ProgressBar",
    "ColorPicker",
]

__all__ += _ansi_all
__all__ += _parser_all
__all__ += _widgets_all
__all__ += _serializer_all
__version__ = "0.1.0"

from .parser import *
from .widgets import *
from .helpers import *
from .serializer import *
from .ansi_interface import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at
