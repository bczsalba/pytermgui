"""
pytermgui.widgets.extra
------------------------
author: bczsalba


This submodule provides some extra widgets. The biggest difference
between these and the ones in .base is that these either fully rely on,
or at least partially use the classes provided in .base.
"""

# These classes will have to have more than 7 attributes mostly.
# pylint: disable=too-many-instance-attributes

import string
from typing import Any

from .base import (
    Container,
    Label,
    Widget,
)

from .styles import (
    default_foreground,
    MarkupFormatter,
    apply_markup,
    StyleType,
    CharType,
)
from ..input import keys, getch
from ..helpers import real_length
from ..ansi_interface import foreground, background, reset


__all__ = [
    "Splitter",
    "ColorPicker",
    "InputField",
    "alert",
]


class ColorPicker(Container):
    """A Container that shows the 256 color table"""

    serialized = Widget.serialized + ["grid_cols"]

    def __init__(self, grid_cols: int = 8, **attrs: Any) -> None:
        """Initialize object, set width"""

        super().__init__(**attrs)

        self.grid_cols = grid_cols
        self.forced_width = self.grid_cols * 4 - 1 + self.sidelength
        self.width = self.forced_width

        self._layer_functions = [
            foreground,
            background,
        ]

        self.layer = 0

    def toggle_layer(self, *_: Any) -> None:
        """Toggle foreground/background"""

        self.layer = 1 if self.layer == 0 else 0

    def get_lines(self) -> list[str]:
        """Get color table lines"""

        chars = self.get_char("border")
        assert isinstance(chars, list)
        left_border, _, right_border, _ = chars

        lines = super().get_lines()
        last_line = lines.pop()

        for line in range(256 // self.grid_cols):
            buff = left_border

            for num in range(self.grid_cols):
                col = str(line * self.grid_cols + num)
                if col == "0":
                    buff += "    "
                    continue

                buff += self._layer_functions[self.layer](f"{col:>3}", col) + " "

            buff = buff[:-1]
            lines.append(buff + "" + right_border)

        lines.append(last_line)

        return lines

    def debug(self) -> str:
        """Show identifiable information on widget"""

        return Widget.debug(self)


class Splitter(Container):
    """A Container-like object that allows stacking Widgets horizontally"""

    chars: dict[str, CharType] = {"separator": " | "}

    styles: dict[str, StyleType] = {
        "separator": apply_markup,
    }

    def __init__(self, *widgets: Widget, **attrs: Any) -> None:
        """Initialize Splitter, add given elements to it"""

        super().__init__(*widgets, **attrs)
        self.parent_align = Widget.PARENT_RIGHT

    @staticmethod
    def _get_offset(widget: Widget, target_width: int) -> tuple[int, int]:
        """Get alignment offset of a widget"""

        if widget.parent_align is Widget.PARENT_CENTER:
            total = target_width - widget.width
            padding = total // 2
            return padding + total % 2, padding

        if widget.parent_align is Widget.PARENT_RIGHT:
            return target_width - widget.width, 0

        # Default to left-aligned
        return 0, target_width - widget.width + 1

    def get_lines(self) -> list[str]:
        """Get lines of all objects"""

        separator = self.get_char("separator")
        separator_style = self.get_style("separator")

        assert isinstance(separator, str)
        separator_length = real_length(separator)

        lines = []
        widget_lines = []
        self.mouse_targets = []

        target_width = self.width // len(self._widgets) - len(self._widgets) + 1
        total_width = 0

        for widget in self._widgets:
            left, right = self._get_offset(widget, target_width)
            widget.pos = (self.pos[0] + total_width + left, self.pos[1])

            line = widget.get_lines()[0].strip()
            if widget.forced_width is None:
                widget.width = real_length(line)

            inner_lines = []
            for line in widget.get_lines():
                inner_lines.append(left * " " + line + right * " ")

            widget_lines.append(inner_lines)
            total_width += target_width + separator_length

            self.mouse_targets += widget.mouse_targets

        for horizontal in zip(*widget_lines):
            lines.append((reset() + separator_style(separator)).join(horizontal))

        for target in self.mouse_targets:
            target.adjust()

        return lines

    def debug(self) -> str:
        """Return identifiable information"""

        return super().debug().replace("Container", "Splitter")


class InputField(Label):
    """An element to display user input"""

    styles = {
        "value": default_foreground,
        "cursor": MarkupFormatter("[inverse]{item}"),
        "fill": MarkupFormatter("[@blue]{item}"),
    }

    def __init__(self, value: str = "", prompt: str = "", **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(prompt + value, **attrs)
        self._is_bindable = True

        self.parent_align = 0

        self.value = value
        self.prompt = prompt
        self.cursor = real_length(self.value)
        self.is_selectable = True

    @property
    def selectables_length(self) -> int:
        """Get length of selectables in object"""

        return 1

    @property
    def cursor(self) -> int:
        """Get cursor"""

        return self._cursor

    @cursor.setter
    def cursor(self, value: int) -> None:
        """Set cursor as an always-valid value"""

        self._cursor = max(0, min(value, real_length(self.value)))

    def send(self, key: str) -> bool:
        """Handle keypress, return True if success, False if failure"""

        def _run_callback() -> None:
            """Call callback if `keys.ANY_KEY` is bound"""

            if keys.ANY_KEY in self._bindings:
                method, _ = self._bindings[keys.ANY_KEY]
                method(self, key)

        if self.execute_binding(key):
            return True

        if key == keys.BACKSPACE and self.cursor > 0:
            left = self.value[: self.cursor - 1]
            right = self.value[self.cursor :]
            self.value = left + right

            self.cursor -= 1

            _run_callback()

        elif key in [keys.LEFT, keys.CTRL_B]:
            self.cursor -= 1

        elif key in [keys.RIGHT, keys.CTRL_F]:
            self.cursor += 1

        # Ignore unhandled non-printing keys
        elif key == keys.ENTER or key not in string.printable:
            return False

        # Add character
        else:
            left = self.value[: self.cursor] + key
            right = self.value[self.cursor :]

            self.value = left + right
            self.cursor += len(key)
            _run_callback()

        return True

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        cursor_style = self.get_style("cursor")
        fill_style = self.get_style("fill")

        # Cache value to be reset later
        old = self.value

        # Create sides separated by cursor
        left = fill_style(self.value[: self.cursor])
        right = fill_style(self.value[self.cursor + 1 :])

        # Assign cursor character
        if self.selected_index is None:
            cursor_char = ""
        elif len(self.value) > self.cursor:
            cursor_char = self.value[self.cursor]
        else:
            cursor_char = " "

        # Set new value, get lines using it
        self.value = self.prompt + left + cursor_style(cursor_char) + right
        lines = super().get_lines()

        # Set old value
        self.value = old

        # Reset & set mouse targets
        self.mouse_targets = []
        self.define_mouse_target(0, 0, height=self.height)

        return [
            line + fill_style((self.width - real_length(line) + 1) * " ")
            for line in lines
        ]


def alert(data: Any) -> None:
    """Create a dismissible dialogue and pause execution"""

    root = Container()
    root += Label("[210 italic bold]Alert!")
    root += Label()
    root += Label(str(data))

    root.center()
    root.print()
    getch()
    root.wipe()
