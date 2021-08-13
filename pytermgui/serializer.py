"""
pytermgui.serializer
--------------------
author: bczsalba


This submodule holds the Serializer() class, which allows
saving & loading widgets.
"""

from __future__ import annotations

import json
from typing import Any, Type, IO, Dict

from . import widgets
from .parser import ansi
from .widgets.base import Widget
from .widgets.styles import default_foreground, CharType

WidgetDict = Dict[str, Type[Widget]]

__all__ = ["serializer"]


class _Serializer:
    """A class to facilitate loading & dumping widgets.

    By default it is only aware of pytermgui objects, however
    if needed it can be made aware of custom widgets using the
    `.register(cld)` method.

    It can dump all types of object, but can only load known ones.

    All styles (except for char ones) are converted to markup
    during the dump process. This is done to make the end-result
    more readable, as well as more universally usable. As a result,
    all elements use `markup_style` for their affected styles."""

    def __init__(self) -> None:
        """Set up known widgets"""

        self.known_widgets = self.get_widgets()

    @staticmethod
    def get_widgets() -> WidgetDict:
        """Get all widgets from the module"""

        known = {}
        for name, item in vars(widgets).items():
            if not isinstance(item, type):
                continue

            if issubclass(item, Widget):
                known[name] = item

        return known

    @staticmethod
    def dump_to_dict(obj: Widget) -> dict[str, Any]:
        """Dump widget to a dict, alias for obj.serialize()

        Todo: this method should also dump custom tags"""

        return obj.serialize()

    def register(self, cls: Widget) -> None:
        """Make object aware of a custom widget class, so
        it can be serialized."""

        self.known_widgets[cls.__name__] = type(cls)

    def load_from_dict(self, data: dict[str, Any]) -> Widget:
        """Load a widget from a dictionary"""

        def _apply_markup(value: CharType) -> CharType:
            """Apply markup style to obj's key"""

            formatted: CharType
            if isinstance(value, list):
                formatted = [ansi(val) for val in value]
            else:
                formatted = ansi(value)

            return formatted

        obj_class_name = data.get("type")
        if obj_class_name is None:
            raise ValueError("Object with type None could not be loaded.")

        if obj_class_name not in self.known_widgets:
            raise ValueError(
                f'Object of type "{obj_class_name}" is not known!'
                + f" Register it with `serializer.register({obj_class_name})`."
            )

        del data["type"]

        obj_class = self.known_widgets.get(obj_class_name)
        assert obj_class is not None

        obj = obj_class()

        for key, value in data.items():
            if key == "_widgets":
                for widget in value:
                    new = self.load_from_dict(widget)
                    assert hasattr(obj, "__iadd__")

                    # this object can be added to, since
                    # it has an __iadd__ method.
                    obj += new  # type: ignore

                continue

            # chars are converted to ansi separately,
            # then their corresponding style is set
            # to default_foreground. Look into why this
            # is needed.
            if key == "chars":
                chars: dict[str, CharType] = {}
                for name, char in value.items():
                    chars[name] = _apply_markup(char)
                    obj.set_style(name, default_foreground)

                setattr(obj, "chars", chars)
                continue

            setattr(obj, key, value)

        return obj

    def load_from_file(self, file: IO[str]) -> Widget:
        """Load widget from a file object"""

        return self.load_from_dict(json.load(file))

    def dump_to_file(
        self, obj: Widget, file: IO[str], **json_args: dict[str, Any]
    ) -> None:
        """Dump widget to a file object"""

        data = self.dump_to_dict(obj)
        if "separators" not in json_args:
            # this is a sub-element of a dict[str, Any], so this
            # should work.
            json_args["separators"] = (",", ":")  # type: ignore

        # ** is supposed to be a dict, not a positional arg
        json.dump(data, file, **json_args)  # type: ignore


serializer = _Serializer()
