"""
A simple yet powerful TUI framework for your Python (3.7+) applications.

There is a couple of parts that make up this module, all building on top
of eachother to achieve the final result. Your usage depends on which part
of the library you use. I will provide an example of usage for each.

.. include:: ../docs/getting_started.md
"""

# https://github.com/python/mypy/issues/4930
# mypy: ignore-errors

from __future__ import annotations

import sys
from typing import Any, Optional

from .enums import *
from .parser import *
from .colors import *
from .widgets import *
from .helpers import *
from .terminal import *
from .inspector import *
from .exporters import *
from .animations import *
from .serializer import *
from .exceptions import *
from .fancy_repr import *
from .prettifiers import *
from .highlighters import *
from .file_loaders import *
from .ansi_interface import *
from .window_manager import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at, mouse_handler

# Silence warning if running as standalone module
if "-m" in sys.argv:  # pragma: no cover
    import warnings

    warnings.filterwarnings("ignore")

__version__ = "6.2.0"


def auto(data: Any, **widget_args: Any) -> Optional[Widget | list[Splitter]]:
    """Creates a widget from specific data structures.

    This conversion includes various widget classes, as well as some shorthands for
    more complex objects.  This method is called implicitly whenever a non-widget is
    attempted to be added to a Widget.


    Args:
        data: The structure to convert. See below for formats.
        **widget_args: Arguments passed straight to the widget constructor.

    Returns:
        The widget or list of widgets created, or None if the passed structure could
        not be converted.

    <br>
    <details style="text-align: left">
        <summary style="all: revert; cursor: pointer">Data structures:</summary>

    `pytermgui.widgets.base.Label`:

    * Created from `str`
    * Syntax example: `"Label value"`

    `pytermgui.widgets.extra.Splitter`:

    * Created from `tuple[Any]`
    * Syntax example: `(YourWidget(), "auto_syntax", ...)`

    `pytermgui.widgets.extra.Splitter` prompt:

    * Created from `dict[Any, Any]`
    * Syntax example: `{YourWidget(): "auto_syntax"}`

    `pytermgui.widgets.buttons.Button`:

    * Created from `list[str, pytermgui.widgets.buttons.MouseCallback]`
    * Syntax example: `["Button label", lambda target, caller: ...]`

    `pytermgui.widgets.buttons.Checkbox`:

    * Created from `list[bool, Callable[[bool], Any]]`
    * Syntax example: `[True, lambda checked: ...]`

    `pytermgui.widgets.buttons.Toggle`:

    * Created from `list[tuple[str, str], Callable[[str], Any]]`
    * Syntax example: `[("On", "Off"), lambda new_value: ...]`
    </details>

    Example:

    ```python3
    from pytermgui import Container
    form = (
        Container(id="form")
        + "[157 bold]This is a title"
        + ""
        + {"[72 italic]Label1": "[210]Button1"}
        + {"[72 italic]Label2": "[210]Button2"}
        + {"[72 italic]Label3": "[210]Button3"}
        + ""
        + ["Submit", lambda _, button, your_submit_handler(button.parent)]
    )
    ```
    """
    # In my opinion, returning immediately after construction is much more readable.
    # pylint: disable=too-many-return-statements

    # Nothing to do.
    if isinstance(data, Widget):
        # Set all **widget_args
        for key, value in widget_args.items():
            setattr(data, key, value)

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
        if isinstance(label, tuple):
            assert len(label) == 2
            return Toggle(label, onclick, **widget_args)

        return Button(label, onclick, **widget_args)

    # prompt splitter
    if isinstance(data, dict):
        rows: list[Splitter] = []

        for key, value in data.items():
            left = auto(key, parent_align=HorizontalAlignment.LEFT)
            right = auto(value, parent_align=HorizontalAlignment.RIGHT)

            rows.append(Splitter(left, right, **widget_args))

        if len(rows) == 1:
            return rows[0]

        return rows

    return None


# Alternative binding for the `auto` method
Widget.from_data = staticmethod(auto)
