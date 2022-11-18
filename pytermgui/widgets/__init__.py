"""The widget system."""

from __future__ import annotations

from typing import Optional, Type, Union

from . import boxes
from .base import *
from .button import Button
from .checkbox import Checkbox
from .collapsible import *
from .color_picker import ColorPicker
from .containers import *
from .fancy_repr import FancyReprWidget
from .frames import *
from .inline import inline
from .input_field import InputField
from .keyboard_button import KeyboardButton
from .pixel_matrix import *
from .slider import Slider
from .styles import *
from .toggle import Toggle

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
