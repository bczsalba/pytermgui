"""
pytermgui.widgets
-----------------
author: bczsalba


This module provides some widgets to be used in pytermgui.
The basic usage is to create a main Container(), and use
the `+=` operator to append elements to it.
"""

from typing import Optional, Union, Type

from . import boxes
from .base import __all__ as _base_all
from .extra import __all__ as _extra_all
from .styles import __all__ as _styles_all
from .buttons import __all__ as _buttons_all

from .base import *
from .extra import *
from .styles import *
from .buttons import *

WidgetType = Union[Widget, Type[Widget]]


__all__ = ["boxes", "WidgetType", "get_widget", "get_id"] + (
    _base_all + _extra_all + _styles_all + _buttons_all
)


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
        """Remove widget from self._widget

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
get_widget = _manager.get_widget
get_id = _manager.get_id
Widget.manager = _manager
