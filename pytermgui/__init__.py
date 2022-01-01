"""
A simple yet powerful TUI framework for your Python (3.6+) applications.

There is a couple of parts that make up this module, all building on top
of eachother to achieve the final result. Your usage depends on which part
of the library you use. I will provide an example of usage for each.

## Low level

At the base, there is `ansi_interface` and `input`, handling terminal APIs
for output and input respectively. This is the lowest-level layer of the
library.

```python3
import pytermgui as ptg

ptg.set_alt_buffer()
print("This text will be discarded on '\n' input.")
while ptg.getch() != "\n":
    print("Wrong key.")
ptg.unset_alt_buffer()
```


## Helper level

On top of that, there is the helper layer, including things like `helpers`,
`context_managers` and the kind. These provide no extra functionality, only
combine functions defined below them in order to make them more usable.


```python3
import pytermgui as ptg

for line in ptg.break_line(
    "This is some \033[1mlong\033[0m and \033[38;5;141mstyled\033[0m text.",
    limit=10,
)
```


## High level

Building on all that is the relatively high level `widgets` module. This
part uses things from everything defined before it to create a visually
appealing interface system. It introduces a lot of its own APIs and 
abstractions, and leaves all the parts below it free of cross-layer
dependencies.

The highest layer of the library is for `window_manager`. This layer combines
parts from everything below. It introduces abstractions on top of the `Widget`
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

__version__ = "0.4.1"


def auto(  # pylint: disable=R0911
    data: Any, **widget_args: Any
) -> Optional[Union[Widget, list[Splitter]]]:
    """Create a Widget from data

    This conversion includes various widget classes, as well as some shorthands for
    more complex objects.

    Currently supported:
        - Label (str):
            + `"This becomes a label [141] with markup!"`
            + value: str   -> Label(value, **attrs)

        - Splitter (tuple):
            + `("left", Container("1", "2"), "right")`
            + tuple[item1: Any, item2: Any] -> Splitter(item1, item2, ..., **attrs)

        - Various button types (list):
            + Button:
                * `["Button Label", lambda target, caller: input(caller)]`
                * list[label: str, onclick: ButtonCallback]  -> Button(label, onclick, **attrs)

            + Checkbox:
                * `[True, lambda checked: input(checked)]`
                * list[default: bool, callback: Callable[[bool], Any]]  -> \
                        Checkbox(default, callback, **attrs)

            + Toggle:
                * `[("Default", "Modified"), lambda new_value: input(new_value)]`
                * list[tuple[state1: str, state2: str], callback: Callable[[str], Any] -> \
                        Toggle((state1, state2), callback)

        - Splitter prompt:
            + `{"key": InputField("value")}`
            + dict[left: Any, right: Any]  -> (
                Splitter(
                    auto(left, parent_align=0),
                    auto(right, parent_align=2),
                    **attrs
                )
            )

    This method is
    called implicitly whenever a non-widget is attempted to be added to
    a Widget. It returns None in case of a failure

    Example:
        >>> from pytermgui import Container
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
