"""
This module provides commonly used enumerations for the library.
It also has a class implementing Enum-s with default values. All Enums
below subclass it, meaning you can use their `get_default()` methods to get
the globally set default value.

To modify defaults, use the `defaults` dictionary.
"""

# This file is an absolute mess to mypy-correctly type.
# It is still typed well enough for a human to read, but
# I could not make mypy accept it without making the code
# horrible to read and edit.
#
# mypy: ignore-errors

from __future__ import annotations

from typing import Type
from enum import IntEnum, auto as _auto

defaults: dict[IntEnum, Type[IntEnum]] = {}

__all__ = ["SizePolicy", "WidgetAlignment"]


class DefaultEnum(IntEnum):
    """An Enum class that can return its default value"""

    @classmethod
    def get_default(cls) -> IntEnum | None:
        """Get default value"""

        return defaults.get(cls)


class SizePolicy(DefaultEnum):
    """Values according to which Widget sizes are assigned"""

    FILL = _auto()
    """Inner widget will take up as much width as possible"""

    STATIC = _auto()
    """Inner widget will take up an exact amount of width"""

    RELATIVE = _auto()  # TODO: Implement this
    """Not implemented: Inner widget will take up a percentage of the available width"""


class CenteringPolicy(DefaultEnum):
    """Policies to center `Container` according to"""

    ALL = _auto()
    VERTICAL = _auto()
    HORIZONTAL = _auto()


class WidgetAlignment(DefaultEnum):
    """Policies to align widgets by

    These are applied by the parent object, and are
    relative to them."""

    LEFT = 0
    CENTER = 1
    RIGHT = 2


defaults[SizePolicy] = SizePolicy.FILL
defaults[CenteringPolicy] = CenteringPolicy.ALL
defaults[WidgetAlignment] = WidgetAlignment.CENTER
