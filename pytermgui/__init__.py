"""
pytermgui
---------
author: bczsalba


A simple yet powerful TUI framework for your Python (3.9+) applications
"""

# https://github.com/python/mypy/issues/4930
# mypy: ignore-errors

from typing import Union, Any, Optional

from .window_manager import __all__ as _manager_all
from .exceptions import __all__ as _exceptions_all
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
from .exceptions import *
from .ansi_interface import *
from .window_manager import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at, mouse_handler

# Build `__all__` for star import (which you really shouldn't do.)
__all__ = ["__version__"]
__all__ += _ansi_all
__all__ += _parser_all
__all__ += _manager_all
__all__ += _widgets_all
__all__ += _inspector_all
__all__ += _serializer_all
__all__ += _exceptions_all
__version__ = "0.2.0"


def _macro_align(item: str) -> str:
    """Use f-string alignment on a markup plain.

    Syntax: "[!align]width:aligment text" -> [!align]30:left hello"""

    # TODO: A better syntax for macros might be !align(30:left) or
    #       !align_30:left.

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


def auto(  # pylint: disable=R0911
    data: Any, **widget_args: Any
) -> Optional[Union[Widget, list[Splitter]]]:
    """Create a Widget from data

    This conversion includes various widget classes, as well as some shorthands for
    more complex objects.

    Currently supported:
        - Label (str):
             + value: str   -> Label(value, **attrs)

        - Splitter (tuple):
             + tuple[item1: Any, item2: Any] -> Splitter(item1, item2, ..., **attrs)

        - buttons (list):
             + default:
                 * list[label: str, onclick: ButtonCallback]  -> Button(label, onclick, **attrs)

             + Checkbox:
                 * list[default: bool, callback: Callable[[bool], Any]]  ->
                     Checkbox(default, callback, **attrs)

             + Toggle:
                 * list[tuple[state1: str, state2: str], callback: Callable[[str], Any] ->
                     Toggle((state1, state2), callback)

        - prompt splitter:
            + dict[left: Any, right: Any]  -> (
                Splitter(
                    auto(left, parent_align=0),
                    auto(right, parent_align=2),
                    **attrs
                )
            )

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
        Container(Label(...), Label(...), Splitter(...), Splitter(...), Splitter(...), ...)

    Note on pylint: In my opinion, returning immediately after construction is much more readable.
    """

    # Nothing to do.
    if isinstance(data, Widget):
        return data

    # Label
    if isinstance(data, str):
        return Label(data, **widget_args)

    # Splitter
    if isinstance(data, tuple):
        return Splitter(*data, **widget_args)

    # buttons
    if isinstance(data, list):
        label = data[0]
        onclick = None
        if len(data) > 1:
            onclick = data[1]

        # Checkbox
        if isinstance(label, bool):
            return Checkbox(onclick, checked=label, **widget_args)

        # Toggle
        if isinstance(label, list):
            assert len(label) == 2
            return Toggle(label, onclick, **widget_args)

        return Button(label, onclick, **widget_args)

    # prompt splitter
    if isinstance(data, dict):
        rows: list[Splitter] = []

        for key, value in data.items():
            left = auto(key, parent_align=0)
            right = auto(value, parent_align=2)

            rows.append(Splitter(left, right, **widget_args))

        if len(rows) == 1:
            return rows[0]

        return rows

    return None


# Built-in macro definitions
define_macro("!strip", strip_ansi)
define_macro("!strip_fg", _macro_strip_fg)
define_macro("!strip_bg", _macro_strip_bg)
define_macro("!align", _macro_align)
define_macro("!markup", markup)

# Alternative binding for the `auto` method
Widget.from_data = staticmethod(auto)
