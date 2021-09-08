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

from __future__ import annotations

import string
from typing import Any
from itertools import zip_longest

from .base import Container, Label, Widget, MouseTarget

from .styles import (
    default_foreground,
    MarkupFormatter,
    apply_markup,
    StyleType,
    CharType,
)
from ..input import keys, getch
from ..helpers import real_length
from ..ansi_interface import foreground, background, reset, MouseAction, MouseEvent


__all__ = ["Splitter", "ColorPicker", "InputField", "Slider", "alert"]


class ColorPicker(Container):
    """A Container that shows the 256 color table"""

    serialized = Widget.serialized + ["grid_cols"]

    def __init__(self, grid_cols: int = 8, **attrs: Any) -> None:
        """Initialize object, set width"""

        super().__init__(**attrs)

        self.grid_cols = grid_cols
        self.forced_width = self.grid_cols * 4 - 1 + self.sidelength
        self.width = self.forced_width

        self._layer_functions = [foreground, background]

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
    styles: dict[str, StyleType] = {"separator": apply_markup}

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

        # TODO: Rewrite this, it STILL doesn't work.

        separator = self.get_char("separator")

        assert isinstance(separator, str)
        separator_length = real_length(separator)

        # Apply style
        separator = self.get_style("separator")(separator)

        lines = []
        widget_lines: list[str] = []
        self.mouse_targets = []

        error = 1 if self.width % len(self._widgets) else 0

        target_width = self.width // len(self._widgets) - len(self._widgets) + error
        total_width = 0

        line = ""
        for widget in self._widgets:
            left, right = self._get_offset(widget, target_width)
            widget.pos = (self.pos[0] + total_width + left, self.pos[1])

            if widget.forced_width is None:
                widget.width = real_length(widget.get_lines()[0])

            widget_lines.append([])  # type: ignore
            for line in widget.get_lines():
                widget_lines[-1].append(left * " " + line + right * " ")

            total_width += target_width + separator_length

            self.mouse_targets += widget.mouse_targets

        last_line = real_length(line)

        # TODO: This falls apart a lot.
        filler_len = target_width if target_width > last_line else last_line

        for horizontal in zip_longest(*widget_lines, fillvalue=" " * filler_len):
            lines.append((reset() + separator).join(horizontal))

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
        "fill": MarkupFormatter("[@243]{item}"),
    }

    is_bindable = True

    def __init__(self, value: str = "", prompt: str = "", **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(prompt + value, **attrs)

        self.parent_align = 0

        self.value = value
        self.prompt = prompt
        self.cursor = real_length(self.value)

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

    def handle_key(self, key: str) -> bool:
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

    def handle_mouse(
        self, event: MouseEvent, target: MouseTarget | None = None
    ) -> bool:
        """Handle mouse events"""

        action, pos = event

        # Ignore mouse release events
        if action is MouseAction.RELEASE:
            return True

        # Set cursor to mouse location
        if action is MouseAction.LEFT_CLICK:
            self.cursor = pos[0] - self.pos[0]
            return True

        return super().handle_mouse(event, target)

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
        self.width += 2
        lines = super().get_lines()

        # Set old value
        self.value = old
        self.width -= 2

        # Reset & set mouse targets
        self.mouse_targets = []
        self.define_mouse_target(0, -1, height=self.height)

        return [
            line + fill_style((self.width - real_length(line) + 1) * " ")
            for line in lines
        ]


class Slider(Widget):
    """A Widget to display & configure scalable data

    By default, this Widget will act like a slider you might find in a
    settings page, allowing percentage-based selection of magnitude.
    Using `WindowManager` it can even be dragged around by the user using
    the mouse.

    However, setting the `Slider.locked` flag will disable that behaviour,
    and freeze the `Widget` to its current value. The cursor is hidden, and
    mouse inputs are unhandled.

    The `Slider.show_percentage` flag controls whether to display the percentage
    meter to the right side of the `Slider`.
    """

    chars = {
        "endpoint": "",
        "line": "─",
        "cursor": "█",
    }

    styles = {
        "filled": lambda _, item: len(item) * "▇",
        "unfilled": default_foreground,
        "cursor": default_foreground,
        "highlight": MarkupFormatter("[246]{item}"),
    }

    keys = {
        "increase": {keys.RIGHT, keys.CTRL_F, "l", "+"},
        "decrease": {keys.LEFT, keys.CTRL_B, "h", "-"},
    }

    def __init__(
        self,
        onchange: Callable[[float], Any] | None = None,
        locked: bool = False,
        show_counter: bool = True,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.width = 10

        self.locked = locked
        self.show_counter = show_counter
        self.onchange = onchange

        self._value = 0.0
        self._display_value = 0
        self._available = self.width - 5

    @property
    def selectables_length(self) -> int:
        """Return count of selectables"""

        if self.locked:
            return 0
        return 1

    @property
    def value(self) -> float:
        """Get float value"""

        return self._display_value / self._available

    def handle_mouse(
        self, event: MouseEvent, target: MouseTarget | None = None
    ) -> bool:
        """Change slider position"""

        action, pos = event

        # Disallow changing state when Slider is locked
        if not self.locked:
            if action is MouseAction.RELEASE:
                self.selected_index = None
                return True

            if action in [MouseAction.LEFT_DRAG, MouseAction.LEFT_CLICK]:
                self._display_value = max(
                    0, min(pos[0] - self.pos[0] + 1, self._available)
                )
                self.selected_index = 0

                if self.onchange is not None:
                    self.onchange(self.value)

                return True

        return super().handle_mouse(event, target)

    def handle_key(self, key: str) -> bool:
        """Change slider position with keys"""

        if key in self.keys["decrease"]:
            self._display_value -= 1

            if self.onchange is not None:
                self.onchange(self.value)
            return True

        if key in self.keys["increase"]:
            self._display_value += 1

            if self.onchange is not None:
                self.onchange(self.value)
            return True

        return False

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        # Get characters
        line_char = self.get_char("line")
        assert isinstance(line_char, str)

        endpoint_char = self.get_char("endpoint")
        assert isinstance(endpoint_char, str)

        cursor_char = self.get_char("cursor")
        assert isinstance(cursor_char, str)

        # Clamp value
        self._display_value = max(
            0, min(self._display_value, self.width, self._available)
        )

        # Only show cursor if not locked
        if self.locked:
            cursor_char = ""

        # Only highlight cursor if currently selected
        if self.selected_index != 0:
            cursor_char = self.get_style("highlight")(cursor_char)

        # Construct left side
        left = (self._display_value - real_length(cursor_char) + 1) * line_char
        left = self.get_style("filled")(left) + cursor_char

        # Define mouse target
        self.mouse_targets = []
        self.define_mouse_target(-1, 0, height=1)

        # Get counter string
        counter = ""
        if self.show_counter:
            percentage = (self._display_value * 100) // self._available
            counter = f"{str(percentage) + '%': >5}"

        # Construct final string
        self._available = self.width - len(counter) - real_length(endpoint_char)
        line_length = self._available - self._display_value

        return [left + line_length * line_char + endpoint_char + counter]


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
