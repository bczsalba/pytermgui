"""
pytermgui
---------
author: bczsalba


A simple yet powerful TUI framework for your Python (3.9+) applications
"""

from typing import Union, Any, Optional

from .window_manager import __all__ as _manager_all
from .serializer import __all__ as _serializer_all
from .ansi_interface import __all__ as _ansi_all
from .inspector import __all__ as _inspector_all
from .widgets import __all__ as _widgets_all
from .parser import __all__ as _parser_all

from .parser import *
from .widgets import *
from .helpers import *
from .inspector import *
from .serializer import *
from .ansi_interface import *
from .window_manager import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at, mouse_handler

# TODO: Support __all__
__all__ = ["__version__"]

__all__ += _ansi_all
__all__ += _parser_all
__all__ += _manager_all
__all__ += _widgets_all
__all__ += _inspector_all
__all__ += _serializer_all
__version__ = "0.1.4"


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


def _macro_strip_fg(item: str) -> str:
    """Strip foreground color from item"""

    return ansi("[/fg]" + item)


def _macro_strip_bg(item: str) -> str:
    """Strip foreground color from item"""

    return ansi("[/bg]" + item)


def auto(
    data: Union[list[str], dict[str, str], str], **widget_args: Any
) -> Optional[Widget]:
    """Create PyTermGUI widget automatically from data

    Currently supported:
        - str   -> Label(data)
        - list  -> ListView(data)
        - dict  -> Container(Prompt(), ...)
        - tuple -> Splitter(*data)

    If Widget.ALLOW_TYPE_CONVERSION is True (default), this method is
    called implicitly whenever a non-widget is attempted to be added to
    a Widget.

    Example:
        >>> from pytermgui import Container, get_widget, clear
        >>> form = (
        ... Container(id="form")
        ... + "[157 bold]This is a title"
        ... + ""
        ... + {"[72 italic]Label1": "[210]Button1"}
        ... + {"[72 italic]Label2": "[210]Button2"}
        ... + {"[72 italic]Label3": "[210]Button3"}
        ... + ""
        ... + ["Submit", lambda _, button, your_submit_handler(button.parent)]
        ... )
        Container(Label(...), Label(...), Splitter(...), Splitter(...), Splitter(...), Label(...), Button(...))
    """

    if isinstance(data, str):
        return Label(data, **widget_args)

    if isinstance(data, list):
        label = data[0]
        onclick = None
        if len(data) > 1:
            onclick = data[1]

        if isinstance(label, bool):
            return Checkbox(onclick, checked=label)

        elif isinstance(label, list):
            assert len(label) == 2
            toggle = Checkbox(onclick)
            toggle.set_char("checked", label[0])
            toggle.set_char("unchecked", label[1])
            toggle.label = label[0]
            return toggle

        return Button(label, onclick, **widget_args)

    if isinstance(data, dict):
        rows: list[Splitter] = []

        for key, value in data.items():
            key.parent_align = 0
            value.parent_align = 2
            rows.append(Splitter(key, value, **widget_args))

        if len(rows) == 1:
            return rows[0]

        return rows

    if isinstance(data, tuple):
        return Splitter(*data, **widget_args)

    return None


# This needs to be here to avoid circular imports
define_macro("!strip", strip_ansi)
define_macro("!strip_fg", _macro_strip_fg)
define_macro("!strip_bg", _macro_strip_bg)
define_macro("!align", _macro_align)
define_macro("!markup", markup)

Widget.from_data = staticmethod(auto)
