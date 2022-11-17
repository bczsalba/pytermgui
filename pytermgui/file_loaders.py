"""
Description
===========

This module provides the library with the capability to load files into Widget-s.

It provides a FileLoader base class, which is then subclassed by various filetype-
specific parsers with their own `parse` method. The job of this method is to take
the file contents as a string, and create a valid json tree out of it.

You can "run" a PTG YAML file by calling `ptg -f <filename>` in your terminal.

**To use any YAML related features, the optional dependency PyYAML is required.**


Implementation details
======================

The main method of these classes is `load`, which takes a file-like object or a string,
parses it and returns a `WidgetNamespace` instance. This can then be used to access all
custom `Widget` definitions in the datafile.

This module highly depends on the `serializer` module. Each file loader uses its own
`Serializer` instance, but optionally take a pre-instantiated Serializer at construction.
As with that module, this one depends on it "knowing" all types of Widget-s you are loading.
If you have custom Widget subclass you would like to use in file-based definitions, use the
`FileLoader.register` method, passing in your custom class as the sole argument.


File structure
==============

Regardless of filetype, all loaded files must follow a specific structure:

```
root
|- config
|   |_ custom global widget configuration
|
|- markup
|   |_ custom markup definitions
|
|- boxes
|   |_ custom box definitions
|
|_ widgets
    |_ custom widget definitions
```

The loading follows the order config -> markup -> boxes -> widgets. It is not necessary to
provide all sections.


Example of usage
================

```yaml
# -- data.yaml --

markup:
    label-style: '141 @61 bold'

boxes:
    WINDOW_BOX: [
        "left --- right",
        "left x right",
        "left --- right",
    ]

config:
    Window:
        styles:
            border: '[@79]{item}'
        box: SINGLE

    Label:
        styles:
            value: '[label-style]{item}'

widgets:
    MyWindow:
        type: Window
        box: WINDOW_BOX
        widgets:
            Label:
                value: '[210 bold]This is a title'

            Label: {}

            Splitter:
                widgets:
                    - Label:
                        parent_align: 0
                        value: 'This is an option'

                    - Button:
                        label: "Press me!"

            Label: {}
            Label:
                value: '[label-style]{item}'
```


```python3
# -- loader.py --

import pytermgui as ptg

with ptg.YamlLoader() as loader, open("data.yaml", "r") as datafile:
    namespace = loader.load(datafile)

with ptg.WindowManager() as manager:
    manager.add(namespace.MyWindow)
    manager.run()

# Alternatively, one could run `ptg -f "data.yaml"` to display all widgets defined.
# See `ptg -h`.
```

"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import IO, Any, Callable, Type

from . import widgets as widgets_m
from .markup import tim
from .serialization import Serializer

YAML_ERROR = None

try:
    import yaml
except ImportError as import_error:
    # yaml is explicitly checked to be None later
    yaml = None  # type: ignore
    YAML_ERROR = import_error


__all__ = ["WidgetNamespace", "FileLoader", "YamlLoader", "JsonLoader"]


@dataclass
class WidgetNamespace:
    """Class to hold data on loaded namespace."""

    # No clue why `widgets` is seen as undefined here,
    # but not in the code below. It only seems to happen
    # in certain pylint configs as well.
    config: dict[
        Type[widgets_m.Widget], dict[str, Any]  # pylint: disable=undefined-variable
    ]
    widgets: dict[str, widgets_m.Widget]
    boxes: dict[str, widgets_m.boxes.Box] = field(default_factory=dict)

    @classmethod
    def from_config(cls, data: dict[Any, Any], loader: FileLoader) -> WidgetNamespace:
        """Creates a namespace from config data.

        Args:
            data: A dictionary of config data.
            loader: The `FileLoader` instance that should be used.

        Returns:
            A new WidgetNamespace with the given config.
        """

        namespace = WidgetNamespace({}, {})
        for name, config in data.items():
            obj = loader.serializer.known_widgets.get(name)
            if obj is None:
                raise KeyError(f"Unknown widget type {name}.")

            namespace.config[obj] = {
                "styles": obj.styles,
                "chars": obj.chars.copy(),
            }

            for category, inner in config.items():
                value: str | widgets_m.styles.MarkupFormatter

                if category not in namespace.config[obj]:
                    setattr(obj, category, inner)
                    continue

                for key, value in inner.items():
                    namespace.config[obj][category][key] = value

        namespace.apply_config()
        return namespace

    @staticmethod
    def _apply_section(
        widget: Type[widgets_m.Widget], title: str, section: dict[str, str]
    ) -> None:
        """Applies configuration section to the widget."""

        for key, value in section.items():
            if title == "styles":
                widget.set_style(key, value)
                continue

            widget.set_char(key, value)

    def apply_to(self, widget: widgets_m.Widget) -> None:
        """Applies namespace config to the widget.

        Args:
            widget: The widget in question.
        """

        def _apply_sections(
            data: dict[str, dict[str, str]], widget: widgets_m.Widget
        ) -> None:
            """Applies sections from data to the widget."""

            for title, section in data.items():
                self._apply_section(type(widget), title, section)

        data = self.config.get(type(widget))
        if data is None:
            return

        _apply_sections(data, widget)

        if hasattr(widget, "_widgets"):
            for inner in widget:
                inner_section = self.config.get(type(inner))

                if inner_section is None:
                    continue

                _apply_sections(inner_section, inner)

    def apply_config(self) -> None:
        """Apply self.config to current namespace."""

        for widget, settings in self.config.items():
            for title, section in settings.items():
                self._apply_section(widget, title, section)

    def __getattr__(self, attr: str) -> widgets_m.Widget:
        """Get widget by name from widget list."""

        if attr in self.widgets:
            return self.widgets[attr]

        return self.__dict__[attr]


class FileLoader(ABC):
    """Base class for file loader objects.

    These allow users to load pytermgui content from a specific filetype,
    with each filetype having their own loaders.

    To use custom widgets with children of this class, you need to call `FileLoader.register`."""

    serializer: Serializer
    """Object-specific serializer instance. In order to use a specific, already created
    instance you need to pass it on `FileLoader` construction."""

    @abstractmethod
    def parse(self, data: str) -> dict[Any, Any]:
        """Parses string into a dictionary used by `pytermgui.serializer.Serializer`.

        This dictionary follows the structure defined above.
        """

    def __init__(self, serializer: Serializer | None = None) -> None:
        """Initialize FileLoader.

        Args:
            serializer: An optional `pytermgui.serializer.Serializer` instance. If not provided, one
                is instantiated for every FileLoader instance.
        """

        if serializer is None:
            serializer = Serializer()

        self.serializer = serializer

    def __enter__(self) -> FileLoader:
        """Starts context manager."""

        return self

    def __exit__(self, _: Any, exception: Exception, __: Any) -> bool:
        """Ends context manager."""

        if exception is not None:
            raise exception

    def register(self, cls: Type[widgets_m.Widget]) -> None:
        """Registers a widget to the serializer.

        Args:
            cls: The widget type to register.
        """

        self.serializer.register(cls)

    def bind(self, name: str, method: Callable[..., Any]) -> None:
        """Binds a name to a method.

        Args:
            name: The name of the method, as referenced in the loaded
                files.
            method: The callable to bind.
        """

        self.serializer.bind(name, method)

    def load_str(self, data: str) -> WidgetNamespace:
        """Creates a `WidgetNamespace` from string data.

        To parse the data, we use `FileLoader.parse`. To implement custom formats,
        subclass `FileLoader` with your own `parse` implementation.

        Args:
            data: The data to parse.

        Returns:
            A WidgetNamespace created from the provided data.
        """

        parsed = self.parse(data)

        # Get & load config data
        config_data = parsed.get("config")
        if config_data is not None:
            namespace = WidgetNamespace.from_config(config_data, loader=self)
        else:
            namespace = WidgetNamespace.from_config({}, loader=self)

        # Create aliases
        for key, value in (parsed.get("markup") or {}).items():
            tim.alias(key, value)

        # Create boxes
        for name, inner in (parsed.get("boxes") or {}).items():
            self.serializer.register_box(name, widgets_m.boxes.Box(inner))

        # Create widgets
        for name, inner in (parsed.get("widgets") or {}).items():
            widget_type = inner.get("type") or name

            box_name = inner.get("box")

            box = None
            if box_name is not None and box_name in namespace.boxes:
                box = namespace.boxes[box_name]
                del inner["box"]

            try:
                namespace.widgets[name] = self.serializer.from_dict(
                    inner, widget_type=widget_type
                )
            except AttributeError as error:
                raise ValueError(
                    f'Could not load "{name}" from data:\n{json.dumps(inner, indent=2)}'
                ) from error

            if box is not None:
                namespace.widgets[name].box = box

        return namespace

    def load(self, data: str | IO) -> WidgetNamespace:
        """Loads data from a string or a file.

        When an IO object is passed, its data is extracted as a string.
        This string can then be passed to `load_str`.

        Args:
            data: Either a string or file stream to load data from.

        Returns:
            A WidgetNamespace with the data loaded.
        """

        if not isinstance(data, str):
            data = data.read()

        assert isinstance(data, str)
        return self.load_str(data)


class JsonLoader(FileLoader):
    """JSON specific loader subclass."""

    def parse(self, data: str) -> dict[Any, Any]:
        """Parse JSON str.

        Args:
            data: JSON formatted string.

        Returns:
            Loadable dictionary.
        """

        return json.loads(data)


class YamlLoader(FileLoader):
    """YAML specific loader subclass."""

    def __init__(self, serializer: Serializer | None = None) -> None:
        """Initialize object, check for installation of PyYAML."""

        if YAML_ERROR is not None:
            raise RuntimeError(
                "YAML implementation module not found. Please install `PyYAML` to use `YamlLoader`."
            ) from YAML_ERROR

        super().__init__()

    def parse(self, data: str) -> dict[Any, Any]:
        """Parse YAML str.

        Args:
            data: YAML formatted string.

        Returns:
            Loadable dictionary.
        """

        assert yaml is not None
        return yaml.safe_load(data)
