"""
pytermgui.widgets
-----------------
author: bczsalba


This module provides some widgets to be used in pytermgui.
The basic usage is to create a main Container(), and use
the `+=` operator to append elements to it.
"""

from typing import Optional, Union, Type
from .base import Widget, Container, Splitter, Prompt, Label
from .extra import ListView, ColorPicker, InputField, ProgressBar
from .styles import *
from . import boxes

WidgetType = Union[Widget, Type[Widget]]

__all__ = [
    "Widget",
    "Splitter",
    "Container",
    "Prompt",
    "Label",
    "ListView",
    "ColorPicker",
    "InputField",
    "ProgressBar",
    "boxes",
    "MarkupFormatter",
    "get_widget",
    "get_id",
]


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
