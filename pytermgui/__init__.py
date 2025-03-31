"""
Welcome to the API reference for **PyTermGUI**, a Python TUI framework with mouse
support, modular widget system, customizable and rapid terminal markup language and
more!
"""

# https://github.com/python/mypy/issues/4930
# mypy: ignore-errors

from __future__ import annotations

import sys
from typing import Any, Optional

from .animations import *
from .ansi_interface import *
from .colors import *
from .context_managers import alt_buffer, cursor_at, mouse_handler
from .enums import *
from .exceptions import *
from .exporters import *
from .fancy_repr import *
from .file_loaders import *
from .helpers import *
from .highlighters import *
from .input import *
from .inspector import *
from .markup import *
from .palettes import *
from .prettifiers import *
from .regex import *
from .serialization import *
from .term import *
from .widgets import *
from .window_manager import *

# Silence warning if running as standalone module
if "-m" in sys.argv:  # pragma: no cover
    import warnings

    warnings.filterwarnings("ignore")

__version__ = "7.7.4"


def auto(data: Any, **widget_args: Any) -> Optional[Widget | list[Splitter]]:
    """Creates a widget from specific data structures.

    This conversion includes various widget classes, as well as some shorthands for
    more complex objects.  This method is called implicitly whenever a non-widget is
    attempted to be added to a Widget.

    You can read up on the syntacies for each builtin widget within the widget
    [documentation](/widgets/builtins).

    Args:
        data: The structure to convert. See below for formats.
        **widget_args: Arguments passed straight to the widget constructor.

    Returns:
        The widget or list of widgets created, or None if the passed structure could
        not be converted.

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
