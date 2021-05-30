"""
pytermgui.serializer
--------------------
author: bczsalba


This submodule holds the Serializer() class, which allows
saving & loading widgets.
"""

import json
from .parser import markup_to_ansi
from typing import Any, Union, Type, IO, Any
from .widgets.styles import markup_style
from . import widgets

WidgetDict = dict[str, Union[widgets.Widget, Type[widgets.Widget]]]

__all__ = [
    "serializer"
]

class _Serializer:
    """"""
    
    def __init__(self) -> None:
        """Set up known widgets"""

        self.known_widgets = self.get_widgets()

    def register(self, cls: widgets.Widget) -> None:
        """Make object aware of a custom widget class, so
        it can be serialized."""

        self.known_widgets[cls.__name__] = cls

    def get_widgets(self) -> WidgetDict:
        """Get all widgets from the module"""

        known = {}
        for name, item in vars(widgets).items():
            if not isinstance(item, type):
                continue

            if issubclass(item, widgets.Widget):
                known[name] = item

        return known

    def load_from_dict(self, data: dict) -> widgets.Widget:
        """Load a widget from a dictionary"""

        def _apply_markup(value: widgets.CharType) -> widgets.CharType:
            """Apply markup style to obj's key"""

            if isinstance(value, list):
                formatted = [markup_to_ansi(val) for val in value]
            else:
                formatted = markup_to_ansi(value)

            return formatted

        obj_class_name = data.get('type')
        if obj_class_name is None:
            raise ValueError("Object with type None could not be loaded.")

        if obj_class_name not in self.known_widgets:
            raise ValueError(
                f"Object of type \"{obj_class_name}\" is not known!"
                + f" Register it with `serializer.register({obj_class_name})`."
            )

        del data['type']

        obj_class = self.known_widgets.get(obj_class_name)
        obj = obj_class()

        for key, value in data.items():
            if key == "_widgets":
                for widget in value:
                    obj += self.load_from_dict(widget)
                continue

            # chars need to be ansi-fied separately,
            # as they don't use markup_style
            # Look into why they *can't* use markup_style
            if key == "chars":
                chars: dict[str, CharType] = {}
                for name, char in value.items():
                    chars[name] = _apply_markup(char)

                setattr(obj, "chars", chars)
                continue

            if key == "styles":
                continue

            setattr(obj, key, value)

        return obj

    def load_from_file(self, file: IO[str]) -> widgets.Widget:
        """Load widget from a file object"""

        return self.load_from_dict(json.load(file))

    def dump_to_dict(self, obj: widgets.Widget) -> dict[str, Any]:
        """Dump widget to a dict, alias for obj.serialize()"""

        return obj.serialize()

    def dump_to_file(self, obj: widgets.Widget, file: IO[str], **json_args: dict[str, Any]) -> None:
        """Dump widget to a file object"""

        data = self.dump_to_dict(obj)
        json.dump(data, file, **json_args)

serializer = _Serializer()
