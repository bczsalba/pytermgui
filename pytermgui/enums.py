"""
pytermgui.enums
---------------
author: bczsalba


This module provides commonly used enumerations for the library.
It also has a class implementing Enum-s with default values. All Enums
below subclass it, meaning you can their `get_default()` methods to get
the global default value.

To modify defaults, use the `defaults` dictionary.
"""

from __future__ import annotations

from enum import Enum, auto as _auto

defaults = {}

__all__ = [
    "SizePolicy",
    "WidgetAlignment",
]


class DefaultEnum(Enum):
    """An Enum class that can return its default value"""

    @classmethod
    def get_default(cls) -> Enum | None:
        """Get default value"""

        return defaults.get(cls)


class SizePolicy(DefaultEnum):
    """Values according to which Widget sizes are assigned

    FILL: keep the Widget's width set exactly to its parent
    STATIC: always use the set `width` value, don't adjust on resize
    RELATIVE: adjust the Widget's size to be a percentage of the parent
    """

    FILL = _auto()
    STATIC = _auto()
    RELATIVE = _auto()  # NOTE: Not implemented


class CenteringPolicy(DefaultEnum):
    """Values to center according to"""

    ALL = _auto()
    VERTICAL = _auto()
    HORIZONTAL = _auto()


class WidgetAlignment(DefaultEnum):
    """Values to align widgets by.

    These are applied by the parent object, and are
    relative to them."""

    LEFT = _auto()
    CENTER = _auto()
    RIGHT = _auto()


defaults[SizePolicy] = SizePolicy.FILL
defaults[CenteringPolicy] = CenteringPolicy.ALL
defaults[WidgetAlignment] = WidgetAlignment.CENTER
