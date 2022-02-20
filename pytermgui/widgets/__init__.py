"""
The widget system.

Basic concept
-------------

Everything starts with the `Widget` class. It represents a single part
of the overarching system. Simple widgets like `Label` simply implement
a `get_lines` method, in which they can come up with what to display as.

The more complex type widget is something like `Container`. This widget holds
other widgets within itself, and uses some fancy logic to display them
in a neat and organized way.


Magic methods
-------------

Most widgets support a selection of magic methods, also known as dunders.
For example, all `Container` children are iterable by default, and allow
adding elements using the `+=` operator. You can also index into them, if
that floats your boat.


Demo
----

There is a lot more information specific to each widget, located in its
documentation. For now, here is a cool showcase of this part of pytermgui.

```python3
import sys
import pytermgui as ptg

with ptg.alt_buffer():
    root = ptg.Container(
        ptg.Label("[210 bold]This is a title"),
        ptg.Label(""),
        ptg.Label("[italic grey]This is some body text. It is very interesting."),
        ptg.Label(),
        ptg.Button("[red]Stop application!", onclick=lambda *_: sys.exit()),
        ptg.Button("[green]Do nothing"),
    )

    root.center().print()

    while True:
        root.handle_key(ptg.getch())
        root.print()
```

<p style="text-align: center">
 <img
  src="https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/widgets/demo.png"
  width=100%>
</p>
"""

from __future__ import annotations

from typing import Optional, Union, Type

from . import boxes

from .base import *
from .styles import *
from .layouts import *
from .interactive import *
from .pixel_matrix import *
from .color_picker import ColorPicker

WidgetType = Union[Widget, Type[Widget]]


class _IDManager:
    """Simple object to store all widgets in a program, and
    allow referencing by id."""

    def __init__(self) -> None:
        """Initialize dict"""

        self._widgets: dict[str, WidgetType] = {}

    def register(self, other: Widget) -> None:
        """Add widget to self._widgets

        This method is meant to be called only internally by Widget."""

        objid = other.id

        if objid is None:
            raise ValueError("Cannot register element with no ID!")

        self._widgets[objid] = other

    def deregister(self, key: str) -> None:
        """Remove widget from self._widgets

        This method is meant to be called only internally by Widget."""

        del self._widgets[key]

    def get_id(self, other: Widget) -> Optional[str]:
        """Check if a widget has been registered"""

        for key, widget in self._widgets.items():
            if widget == other:
                return key

        return None

    def get_widget(self, widget_id: str) -> Optional[WidgetType]:
        """Get widget by id"""

        return self._widgets.get(widget_id)


_manager = _IDManager()
setattr(Widget, "_id_manager", _manager)

get_widget = _manager.get_widget
get_id = _manager.get_id
