"""
`Serializer` class to allow dumping and loading `Widget`-s. This class
uses `Widget.serialize` for each widget.
"""

from __future__ import annotations

import json
from typing import Any, Type, IO, Dict, Callable

from . import widgets
from .parser import markup

from .widgets import CharType
from .widgets.base import Widget
from .window_manager import Window

WidgetDict = Dict[str, Type[Widget]]

__all__ = ["serializer", "Serializer"]


class Serializer:
    """A class to facilitate loading & dumping widgets.

    By default it is only aware of pytermgui objects, however
    if needed it can be made aware of custom widgets using
    `Serializer.register`.

    It can dump any widget type, but can only load ones it knows.

    All styles (except for char styles) are converted to markup
    during the dump process. This is done to make the end-result
    more readable, as well as more universally usable. As a result,
    all widgets use `markup_style` for their affected styles."""

    def __init__(self) -> None:
        """Sets up known widgets."""

        self.known_widgets = self.get_widgets()
        self.known_boxes = vars(widgets.boxes)
        self.register(Window)

        self.bound_methods: dict[str, Callable[..., Any]] = {}

    @staticmethod
    def get_widgets() -> WidgetDict:
        """Gets all widgets from the module."""

        known = {}
        for name, item in vars(widgets).items():
            if not isinstance(item, type):
                continue

            if issubclass(item, Widget):
                known[name] = item

        return known

    @staticmethod
    def dump_to_dict(obj: Widget) -> dict[str, Any]:
        """Dump widget to a dict.

        This is an alias for `obj.serialize`.

        Args:
            obj: The widget to dump.

        Returns:
            `obj.serialize()`.
        """

        return obj.serialize()

    def register_box(self, name: str, box: widgets.boxes.Box) -> None:
        """Registers a new Box type.

        Args:
            name: The name of the box.
            box: The box instance.
        """

        self.known_boxes[name] = box

    def register(self, cls: Type[Widget]) -> None:
        """Makes object aware of a custom widget class, so
        it can be serialized.

        Args:
            cls: The widget type to register.

        Raises:
            TypeError: The object is not a type.
        """

        if not isinstance(cls, type):
            raise TypeError("Registered object must be a type.")

        self.known_widgets[cls.__name__] = cls

    def bind(self, name: str, method: Callable[..., Any]) -> None:
        """Binds a name to a method.

        These method callables are substituted into all fields that follow
        the `method:<method_name>` syntax. If `method_name` is not bound,
        an exception will be raised during loading.

        Args:
            name: The name of the method, as referenced in the loaded
                files.
            method: The callable to bind.
        """

        self.bound_methods[name] = method

    def from_dict(  # pylint: disable=too-many-locals, too-many-branches
        self, data: dict[str, Any], widget_type: str | None = None
    ) -> Widget:
        """Loads a widget from a dictionary.

        Args:
            data: The data to load from.
            widget_type: Substitute for when data has no `type` field.

        Returns:
            A widget from the given data.
        """

        def _apply_markup(value: CharType) -> CharType:
            """Apply markup style to obj's key"""

            formatted: CharType
            if isinstance(value, list):
                formatted = [markup.parse(val) for val in value]
            else:
                formatted = markup.parse(value)

            return formatted

        if widget_type is not None:
            data["type"] = widget_type

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
            if key.startswith("widgets"):
                for inner in value:
                    name, widget = list(inner.items())[0]
                    new = self.from_dict(widget, widget_type=name)
                    assert hasattr(obj, "__iadd__")

                    # this object can be added to, since
                    # it has an __iadd__ method.
                    obj += new  # type: ignore

                continue

            if isinstance(value, str) and value.startswith("method:"):
                name = value[7:]

                if name not in self.bound_methods:
                    raise KeyError(f'Reference to unbound method: "{name}".')

                value = self.bound_methods[name]

            if key == "chars":
                chars: dict[str, CharType] = {}
                for name, char in value.items():
                    chars[name] = _apply_markup(char)

                setattr(obj, "chars", chars)
                continue

            if key == "styles":
                for name, markup_str in value.items():
                    obj.styles[name] = markup_str

                continue

            setattr(obj, key, value)

        return obj

    def from_file(self, file: IO[str]) -> Widget:
        """Loads widget from a file object.

        Args:
            file: An IO object.

        Returns:
            The loaded widget.
        """

        return self.from_dict(json.load(file))

    def to_file(self, obj: Widget, file: IO[str], **json_args: dict[str, Any]) -> None:
        """Dumps widget to a file object.

        Args:
            obj: The widget to dump.
            file: The file object it gets written to.
            **json_args: Arguments passed to `json.dump`.
        """

        data = self.dump_to_dict(obj)
        if "separators" not in json_args:
            # this is a sub-element of a dict[str, Any], so this
            # should work.
            json_args["separators"] = (",", ":")  # type: ignore

        # ** is supposed to be a dict, not a positional arg
        json.dump(data, file, **json_args)  # type: ignore


serializer = Serializer()
