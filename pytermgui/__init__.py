"""
A simple yet powerful TUI framework for your Python (3.7+) applications.

There is a couple of parts that make up this module, all building on top
of eachother to achieve the final result. Your usage depends on which part
of the library you use. I will provide an example of usage for each.


## Low level

At the base, there is `pytermgui.ansi_interface` and `pytermgui.input`, handling terminal APIs
for output and input respectively. This is the lowest-level layer of the
library.

```python3
import pytermgui as ptg

ptg.set_alt_buffer()

print("This terminal will be discarded on '\\n' input.")
while ptg.getch() != "\\n":
    print("Wrong key.")

ptg.unset_alt_buffer()
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init_low.png
    style="width: 80%">
</p>


## Helper level

On top of that, there is the helper layer, including things like `pytermgui.helpers`,
`pytermgui.context_managers` and the kind. These provide no extra functionality, only
combine functions defined below them in order to make them more usable.


```python3
import pytermgui as ptg

text = "This is some \\033[1mlong\\033[0m and \\033[38;5;141mstyled\\033[0m text."
for line in ptg.break_line(text, limit=10):
    print(line)
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init_helper.png
    style="width: 80%">
</p>


## High level

Building on all that is the relatively high level `pytermgui.widgets` module. This
part uses things from everything defined before it to create a visually
appealing interface system. It introduces a lot of its own APIs and
abstractions, and leaves all the parts below it free of cross-layer
dependencies.

The highest layer of the library is for `pytermgui.window_manager`. This layer combines
parts from everything below. It introduces abstractions on top of the `pytermgui.widget`
system, and creates its own featureset.


```python3
import pytermgui as ptg

with ptg.WindowManager() as manager:
    manager.add(
        ptg.Window()
        + "[141 bold]Title"
        + "[grey italic]body text"
        + ""
        + ["Button"]
    )

    manager.run()
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init_high.png
    style="width: 80%">
</p>
"""

# https://github.com/python/mypy/issues/4930
# mypy: ignore-errors

from __future__ import annotations

from typing import Union, Any, Optional
from random import shuffle
import sys

from .enums import *
from .parser import *
from .widgets import *
from .helpers import *
from .inspector import *
from .serializer import *
from .exceptions import *
from .file_loaders import *
from .ansi_interface import *
from .window_manager import *
from .input import getch, keys
from .context_managers import alt_buffer, cursor_at, mouse_handler

# Silence warning if running as standalone module
if "-m" in sys.argv:
    import warnings

    warnings.filterwarnings("ignore")

__version__ = "1.0.0"


def auto(data: Any, **widget_args: Any) -> Optional[Widget | list[Splitter]]:
    """
    ### Create widgets from specific data patterns

    This conversion includes various widget classes, as well as some shorthands for
    more complex objects.

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

    This method is called implicitly whenever a non-widget is attempted to be added to
    a Widget. It returns None in case of a failure

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
            left = auto(key, parent_align=WidgetAlignment.LEFT)
            right = auto(value, parent_align=WidgetAlignment.RIGHT)

            rows.append(Splitter(left, right, **widget_args))

        if len(rows) == 1:
            return rows[0]

        return rows

    return None


# Alternative binding for the `auto` method
Widget.from_data = staticmethod(auto)
