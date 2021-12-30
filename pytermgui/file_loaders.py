"""
pytermgui.file_loaders
----------------------
author: bczsalba


# Description

This module provides the library with the capability to load files into Widget-s.

It provides a FileLoader base class, which is then subclassed by various filetype-
specific parsers with their own `parse` method. The job of this method is to take
the file contents as a string, and create a valid json tree out of it.


# Implementation details

The main method of these classes is `load`, which takes a file-like object or a string,
parses it and returns a `WidgetNamespace` instance. This can then be used to access all
custom `Widget` definitions in the datafile.

This module highly depends on the `serializer` module. Each file loader uses its own
`Serializer` instance, but optionally take a pre-instantiated Serializer at construction.
As with that module, this one depends on it "knowing" all types of Widget-s you are loading.
If you have custom Widget subclass you would like to use in file-based definitions, use the
`FileLoader.register` method, passing in your custom class as the sole argument.


# File structure

Regardless of filetype, all loaded files must follow a specific structure:

```
root
|_ config
|   |_ custom global widget configuration
|
|_ markup
|   |_ custom markup definitions
|
|_ widgets
    |_ custom widget definitions
```

The loading follows the order config -> markup -> widgets. It is not necessary to provide all
sections.


# Example of usage

```yaml
# -- data.yaml --

markup:
    label-style: '141 @61 bold'

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

```python
# -- loader.py --

import pytermgui as ptg

loader = ptg.YamlLoader()
with open("data.yaml", "r") as datafile:
    namespace = loader.load(datafile)

with ptg.WindowManager() as manager:
    manager.add(namespace.MyWindow)
    manager.run()

"""

from __future__ import annotations

from dataclasses import dataclass, field
from abc import abstractmethod, ABC
from typing import Any, Type, IO

import json

from . import widgets
from .parser import markup
from .serializer import Serializer


YAML_ERROR = None
try:
    import yaml
except ImportError as import_error:
    yaml = None
    YAML_ERROR = import_error


__all__ = ["WidgetNamespace", "FileLoader", "YamlLoader", "JsonLoader"]


@dataclass
class WidgetNamespace:
    """Class to hold data on loaded namespace"""

    config: dict[Type[widgets.Widget], dict[str, Any]]
    widgets: dict[str, widgets.Widget]
    boxes: dict[str, widgets.boxes.Box] = field(default_factory=dict)

    @classmethod
    def from_config(cls, data: dict[Any, Any], loader: FileLoader) -> WidgetNamespace:
        """Get namespace from config"""

        namespace = WidgetNamespace({}, {})
        for name, config in data.items():
            obj = loader.serializer.known_widgets.get(name)
            if obj is None:
                raise KeyError(f"Unknown widget type {name}.")

            namespace.config[obj] = {
                "styles": obj.styles.copy(),
                "chars": obj.chars.copy(),
            }

            for category, inner in config.items():
                value: str | widgets.styles.MarkupFormatter

                if category not in namespace.config[obj]:
                    setattr(obj, category, inner)
                    continue

                for key, value in inner.items():
                    namespace.config[obj][category][key] = value

        namespace.apply_config()
        return namespace

    @staticmethod
    def _apply_section(
        widget: Type[widgets.Widget], title: str, section: dict[str, str]
    ) -> None:
        """Apply section of config to widget"""

        for key, value in section.items():
            if title == "styles":
                if isinstance(value, str):
                    widget.set_style(key, widgets.styles.MarkupFormatter(value))
                continue

            widget.set_char(key, value)

    def apply_to(self, widget: widgets.Widget) -> None:
        """Apply namespace config to widget"""

        def _apply_sections(data: dict[str, str], widget: widgets.Widget) -> None:
            """Apply sections from data to widget"""

            for title, section in data.items():
                self._apply_section(widget, title, section)

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
        """Apply self.config to current namespace"""

        for widget, settings in self.config.items():
            for title, section in settings.items():
                self._apply_section(widget, title, section)

    def __getattr__(self, attr: str) -> widgets.Widget:
        """Get widget from namespace widget list by its name"""

        if attr in self.widgets:
            return self.widgets[attr]

        return self.__dict__[attr]


class FileLoader(ABC):
    """Base class for file loader objects.

    These allow users to load pytermgui content from a specific filetype,
    with each filetype having their own loaders.

    To use custom Widget-s with these, you need to call the FileLoader's
    `register()` method."""

    @abstractmethod
    def parse(self, data: str) -> dict[Any, Any]:
        """Parse string into dictionary"""

    def __init__(self, serializer: Serializer | None = None) -> None:
        """Initialize object"""

        if serializer is None:
            serializer = Serializer()

        self.serializer = serializer

    def register(self, cls: Type[widgets.Widget]) -> None:
        """Register a widget to _name_mapping"""

        self.serializer.register(cls)

    def load_str(self, data: str) -> WidgetNamespace:
        """Load string into namespace"""

        parsed = self.parse(data)

        # Get & load config data
        config_data = parsed.get("config")
        if config_data is not None:
            namespace = WidgetNamespace.from_config(config_data, loader=self)
        else:
            namespace = WidgetNamespace.from_config({}, loader=self)

        # Create aliases
        for key, value in (parsed.get("markup") or {}).items():
            markup.alias(key, value)

        # Create boxes
        for name, inner in (parsed.get("boxes") or {}).items():
            self.serializer.register_box(name, widgets.boxes.Box(inner))

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
                    f'Invalid data for widget "{name}": {inner}'
                ) from error

            if box is not None:
                namespace.widgets[name].box = box

        return namespace

    def load(self, data: str | IO) -> WidgetNamespace:
        """Load data from str or file"""

        if not isinstance(data, str):
            data = data.read()

        assert isinstance(data, str)
        return self.load_str(data)


class JsonLoader(FileLoader):
    """Load JSON files for PTG"""

    def parse(self, data: str) -> dict[Any, Any]:
        """Parse JSON str"""

        return json.loads(data)


class YamlLoader(FileLoader):
    """Load YAML files for PTG"""

    def __init__(self, serializer: Serializer | None = None) -> None:
        """Initialize object, check for PyYAML"""

        if YAML_ERROR is not None:
            raise RuntimeError(
                "YAML implementation module not found. Please install `PyYAML` to use `YamlLoader`."
            ) from YAML_ERROR

        super().__init__()

    def parse(self, data: str) -> dict[Any, Any]:
        """Parse YAML str"""

        assert yaml is not None
        return yaml.safe_load(data)
