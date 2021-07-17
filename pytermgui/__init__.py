"""
pytermgui
---------
author: bczsalba


A simple yet powerful TUI framework for your Python (3.9+) applications
"""

from typing import Union, Any, Optional

from .ansi_interface import __all__ as _ansi_all
from .serializer import __all__ as _serializer_all
from .inspector import __all__ as _inspector_all
from .widgets import __all__ as _widgets_all
from .parser import __all__ as _parser_all

# TODO: Support __all__
__all__ = ["__version__"]

__all__ += _ansi_all
__all__ += _parser_all
__all__ += _widgets_all
__all__ += _inspector_all
__all__ += _serializer_all
__version__ = "0.1.2"

from .parser import *
from .widgets import *
from .helpers import *
from .inspector import *
from .serializer import *
from .ansi_interface import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at, mouse_handler


def auto(
    data: Union[list[str], dict[str, str], str], **widget_args: Any
) -> Optional[Widget]:
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

    return None


def _macro_align(item: str) -> str:
    """Use f-string alignment on a markup plain.

    Syntax: "[!align]width:aligment text" -> [!align]30:left hello"""

    # TODO: Allow markup for content in _align_macro

    words = item.split(" ")
    statements = words[0]
    if statements.count(":") == 0:
        return item

    content = " ".join(words[1:])

    width, alignment = statements.split(":")
    aligner = "<" if alignment == "left" else (">" if alignment == "right" else "^")

    return f"{content:{aligner}{width}}"


# This needs to be here to avoid circular imports
define_macro("!strip", strip_ansi)
define_macro("!align", _macro_align)
define_macro("!markup", markup)
