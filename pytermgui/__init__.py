"""
pytermgui
---------
author: bczsalba


A simple and robust terminal UI library, written in Python.
"""

from typing import Union, Any

from .ansi_interface import __all__ as _ansi_all
from .serializer import __all__ as _serializer_all
from .inspector import __all__ as _inspector_all
from .widgets import __all__ as _widgets_all
from .parser import __all__ as _parser_all

# TODO: support __all__
__all__ = [
    "__version__"
]

__all__ += _ansi_all
__all__ += _parser_all
__all__ += _widgets_all
__all__ += _inspector_all
__all__ += _serializer_all
__version__ = "0.1.0"

from .parser import *
from .widgets import *
from .helpers import *
from .inspector import *
from .serializer import *
from .ansi_interface import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at, mouse_handler


def auto(data: Union[list, dict, str], **widget_args: Any) -> Widget:
    """Create PyTermGUI widget automatically from data

    Currently supported:
        - list -> ListView(data)
        - dict -> Container(), elements=[Prompt(), ...]
        - str -> Label(data)
    """

    if isinstance(data, str):
        return Label(data, **widget_args)

    if isinstance(data, list):
        return ListView(data, **widget_args)

    if isinstance(data, dict):
        root = Container()

        for key, value in data.items():
            root += Prompt(key, value, **widget_args)

        return root
