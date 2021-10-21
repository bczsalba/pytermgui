from __future__ import annotations

from typing import Any, Dict, IO
from dataclasses import dataclass
from abc import abstractmethod, ABC

import yaml
import json

from . import widgets
from .parser import markup
from .serializer import Serializer

# We use a module-local Serializer instance so as to
# not muddle with the pre-instantiated global.
SERIALIZER = Serializer()

__all__ = ["WidgetNamespace", "FileLoader", "YamlLoader", "JsonLoader"]


@dataclass
class WidgetNamespace:
    """Class to hold data on loaded namespace"""

    config: dict[Widget, dict[dict[str[str, str]]]]
    widgets: dict[str, Widget]

    @classmethod
    def from_config(cls, data: dict[Any, Any]) -> WidgetNamespace:
        """Get namespace from config"""

        namespace = WidgetNamespace({}, {})
        for name, config in data.items():
            obj = SERIALIZER.known_widgets.get(name)
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
    def _apply_section(widget: Widget, title: str, section: dict[str, str]) -> None:
        """Apply section of config to widget"""

        for key, value in section.items():
            if title == "styles":
                if isinstance(value, str):
                    widget.set_style(key, widgets.styles.MarkupFormatter(value))
                continue

            widget.set_char(key, value)

    def apply_config(self) -> None:
        """Apply self.config to current namespace"""

        for widget, settings in self.config.items():
            for title, section in settings.items():
                self._apply_section(widget, title, section)

    def __getattr__(self, attr: str) -> Callable[None, Widget]:
        """Get copy of widget from namespace widget list by its name"""

        if attr in self.widgets:
            return self.widgets[attr].copy()

        return self.__dict__[attr]


class FileLoader(ABC):
    """Base class for file loader objects.

    These allow users to load pytermgui content from a specific filetype,
    with each filetype having their own loaders.

    To use custom Widget-s with these, you need to call the FileLoader's
    `register()` method."""

    @abstractmethod
    def parse(self, data: str) -> dict[Any]:
        """Parse string into dictionary"""

    def register(self, obj: Widget) -> None:
        """Register a widget to _name_mapping"""

        SERIALIZER.register(name, obj)

    def load_str(self, data: str) -> WidgetNamespace:
        """Load string into namespace"""

        parsed = self.parse(data)

        # Get & load config data
        config_data = parsed.get("config")
        if config_data is not None:
            namespace = WidgetNamespace.from_config(config_data)
        else:
            namespace = WidgetNamespace.from_config(data)

        # Create aliases
        for key, value in parsed.get("markup").items() or []:
            markup.alias(key, value)

        # Create widgets
        for name, inner in parsed.get("widgets").items() or []:
            widget_type = inner.get("type") or name

            namespace.widgets[name] = SERIALIZER.from_dict(
                inner, widget_type=widget_type
            )

        return namespace

    def load(self, data: str | IO) -> WidgetNamespace:
        """Load data from str or file"""

        if not isinstance(data, str):
            data = data.read()

        return self.load_str(data)


class JsonLoader(FileLoader):
    """Load JSON files for PTG"""

    def parse(self, data: str) -> dict[Any]:
        """Parse JSON str"""

        return json.loads(data)


class YamlLoader(FileLoader):
    """Load YAML files for PTG"""

    def parse(self, data: str) -> dict[Any]:
        """Parse YAML str"""

        return yaml.safe_load(data)
