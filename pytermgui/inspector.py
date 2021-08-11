"""
pytermgui.inspector
-------------------
author: bczsalba


This module provides the Inspector() class, and the inspect helper,
to allow inspection of any Python object.

So far it only shows the object's methods, along with their parameters & annotations,
however in the future it will be expanded to support live object data as well.

Todo: live object inspection
Todo: support for module inspection
Todo: handle long items
"""

from typing import Optional, Any
from inspect import signature, getdoc, isclass, ismodule, Signature

from .input import getch
from .parser import ansi

from .widgets.base import Widget, Container, Label
from .context_managers import alt_buffer
from .widgets.boxes import DOUBLE_BOTTOM
from .widgets.styles import MarkupFormatter, StyleType
from .ansi_interface import foreground, screen_height, is_interactive

__all__ = [
    "inspect",
    "Inspector",
]


def create_color_style(color: int) -> StyleType:
    """Create a color style callable"""

    def color_style(_: int, item: str) -> str:
        """Simple style using foreground colors"""

        return foreground(item, color)

    return color_style


def inspect(
    target: Any,
    style: bool = True,
    show_dunder: bool = False,
    show_private: bool = False,
) -> None:
    """Inspect an object"""

    target_height = int(screen_height() * 3 / 4)
    inspector = Inspector()
    inspector.inspect(target, show_dunder=show_dunder, show_private=show_private)

    def handle_scrolling(root: Container, index: int) -> Optional[Container]:
        """Handle scrolling root to index"""

        widgets = []
        current = 0

        for label in inspector[index:]:
            if current > target_height:
                break

            widgets.append(label)
            current += label.height

        if inspector.height < target_height:
            root.forced_height = inspector.height

        else:
            for _ in range(target_height - current):
                widgets.append(Label())

        root.set_widgets(widgets)

        return root

    root = Container()
    root.forced_height = target_height
    root += Label()

    if style:
        builtin_style = inspector.get_style("builtin")
        DOUBLE_BOTTOM.set_chars_of(root)

        corners = root.get_char("corner")
        assert isinstance(corners, list)
        corners[1] = " Inspecting: " + builtin_style(str(target)) + " " + corners[1]
        root.set_char("corner", corners)

        root.set_style("corner", lambda _, item: item)

    handle_scrolling(root, 0)
    scroll = 0

    with alt_buffer(cursor=False):
        root.center()
        root.print()

        while True:
            previous = scroll

            try:
                key = getch()
            except KeyboardInterrupt:
                break

            if inspector.height > target_height:
                if key == "j":
                    scroll += 1

                elif key == "k":
                    scroll -= 1

                scroll = max(0, scroll)

                if not handle_scrolling(root, scroll):
                    scroll = previous

            root.center()
            root.print()

    print("Inspection complete!")
    if is_interactive():
        print(
            ansi(
                "\n[210 bold]Note: [/]"
                + "The Python interactive shell doesn't support hiding input characters,"
                + " so the inspect() experience is not ideal.\n"
                + "Consider using [249]`ptg --inspect`[/fg] instead."
            )
        )


class Inspector(Container):
    """A Container subclass that allows inspection of any Python object"""

    styles = Container.styles | {
        "builtin": MarkupFormatter("[208]{item}"),
        "declaration": MarkupFormatter("[9 bold]{item}"),
        "name": MarkupFormatter("[114]{item}"),
        "string": MarkupFormatter("[142]{item}"),
    }

    _inspectable = [
        "__init__",
        "inspect",
    ]

    def __init__(self, **container_args: Any) -> None:
        """Initialize object and inspect something"""

        super().__init__(**container_args)

        self.styles = type(self).styles.copy()

    @staticmethod
    def _get_signature(target: Any) -> Optional[Signature]:
        """Get signature of target, return None if exception occurs"""

        try:
            return signature(target)

        except (TypeError, ValueError):
            return None

    def _get_docstring(self, target: Any) -> list[str]:
        """Get docstring of target"""

        string_style = self.get_style("string")

        doc = getdoc(target)
        if doc is None:
            return []

        doc = '"""' + doc + '"""'

        lines = []
        for line in doc.splitlines():
            lines.append(string_style(line))

        return lines

    def _get_definition(self, target: Any) -> str:
        """Get definition (def fun(...) / class Cls(...)) of an object"""

        name_style = self.get_style("name")
        declaration_style = self.get_style("declaration")

        elements = [declaration_style("class" if isclass(target) else "def")]

        if hasattr(target, "__name__"):
            obj_name = name_style(getattr(target, "__name__"))

        else:
            obj_name = name_style(type(target).__name__)

        obj_name += "("

        sig = self._get_signature(target)

        if isclass(target) or sig is None:
            parameters = ["..."]

        else:
            parameters = []
            for name, parameter in sig.parameters.items():
                param_str = name

                if name == "self" or parameter.annotation is Signature.empty:
                    parameters.append(param_str)
                    continue

                param_str += ": "
                param_str += self._style_annotation(parameter.annotation)

                if parameter.default is not Signature.empty:
                    param_str += " = "
                    param_str += str(parameter.default)

                parameters.append(param_str)

        obj_name += ", ".join(parameters) + ")"

        if not isclass(target):
            if sig is not None and sig.return_annotation is not Signature.empty:
                obj_name += " -> "
                obj_name += self._style_annotation(sig.return_annotation)

        obj_name += ":"
        elements.append(obj_name)

        return " ".join(elements)

    def _style_annotation(self, annotation: Any) -> str:
        """Style an annotation property"""

        builtin_style = self.get_style("builtin")
        if isinstance(annotation, type):
            return builtin_style(annotation.__name__)

        return builtin_style(str(annotation))

    def inspect(
        self,
        target: Any,
        keep_elements: bool = False,
        show_dunder: bool = False,
        show_private: bool = False,
        _padding: int = 0,
    ) -> Container:
        """Inspect any Python element"""

        if ismodule(target):
            raise NotImplementedError("Modules are not inspectable yet.")

        if not keep_elements:
            self._widgets = []

        definition = Label(
            self._get_definition(target),
            padding=_padding,
            parent_align=Widget.PARENT_LEFT,
        )
        definition.set_style("value", lambda _, item: item)

        # it keeps the same type
        self._add_widget(definition)

        for line in self._get_docstring(target):
            doc = Label(line, padding=_padding + 4, parent_align=Widget.PARENT_LEFT)
            doc.set_style("value", lambda _, item: item)
            self._add_widget(doc)

        if isclass(target):
            self._add_widget(Label())

            if hasattr(target, "_inspectable"):
                functions = [
                    getattr(target, name) for name in getattr(target, "_inspectable")
                ]

            else:
                functions = []
                for name in dir(target):
                    value = getattr(target, name)

                    value_name = getattr(value, "__name__", None)

                    if value_name:
                        if (
                            not show_dunder
                            and value_name.startswith("__")
                            and value_name.endswith("__")
                            and not value_name == "__init__"
                        ):
                            continue

                        if (
                            not show_private
                            and value_name.startswith("_")
                            and not value_name.endswith("__")
                        ):
                            continue

                    if callable(value) and not isinstance(value, type):
                        functions.append(value)

            for function in functions:
                self.inspect(function, keep_elements=True, _padding=_padding + 4)
                self._add_widget(Label())

        return self
