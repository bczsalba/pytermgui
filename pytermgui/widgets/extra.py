"""
Some extra Widgets that rely on and compliment the ones in `widgets/base`.
"""

# These classes will have to have more than 7 attributes mostly.
# pylint: disable=too-many-instance-attributes

from __future__ import annotations

import string
from itertools import zip_longest
from typing import Any, Callable, cast

from .base import Container, Label, Widget, MouseTarget

from . import styles
from ..input import keys
from ..helpers import real_length
from ..enums import WidgetAlignment
from ..ansi_interface import foreground, background, reset, MouseAction, MouseEvent


__all__ = ["InputField", "Splitter", "ColorPicker", "Slider"]


class ColorPicker(Container):
    """A Container that shows the 256 color table"""

    serialized = Widget.serialized + ["grid_cols"]

    def __init__(self, grid_cols: int = 8, **attrs: Any) -> None:
        """Initialize object, set width"""

        super().__init__(**attrs)

        self.grid_cols = grid_cols
        self.width = self.grid_cols * 4 - 1 + self.sidelength

        self._layer_functions = [foreground, background]

        self.layer = 0

    def toggle_layer(self, *_: Any) -> None:
        """Toggle foreground/background"""

        self.layer = 1 if self.layer == 0 else 0

    def get_lines(self) -> list[str]:
        """Get color table lines"""

        chars = self._get_char("border")
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

    chars: dict[str, list[str] | str] = {"separator": " | "}
    styles = {"separator": styles.MARKUP, "fill": styles.BACKGROUND}
    keys = {
        "previous": {keys.LEFT, "h", keys.CTRL_B},
        "next": {keys.RIGHT, "l", keys.CTRL_F},
    }

    parent_align = WidgetAlignment.RIGHT

    def _align(
        self, alignment: WidgetAlignment, target_width: int, line: str
    ) -> tuple[int, str]:
        """Align a line

        r/wordavalanches"""

        available = target_width - real_length(line)
        fill_style = self._get_style("fill")

        char = fill_style(" ")
        line = fill_style(line)

        if alignment == WidgetAlignment.CENTER:
            padding, offset = divmod(available, 2)
            return padding, padding * char + line + (padding + offset) * char

        if alignment == WidgetAlignment.RIGHT:
            return available, available * char + line

        return 0, line + available * char

    def get_lines(self) -> list[str]:
        """Join all widgets horizontally

        Note: This currently has some issues."""

        # An error will be raised if `separator` is not the correct type (str).
        separator = self._get_style("separator")(self._get_char("separator"))  # type: ignore
        assert isinstance(separator, str)
        separator_length = real_length(separator)

        error = self.width % 2
        target_width = self.width // len(self._widgets) - separator_length + 1

        vertical_lines = []
        total_offset = separator_length - 1

        self.mouse_targets = []

        for widget in self._widgets:
            inner = []

            widget.width = target_width

            aligned: str | None = None
            for line in widget.get_lines():
                # See `enums.py` for information about this ignore
                padding, aligned = self._align(
                    cast(WidgetAlignment, widget.parent_align), target_width, line
                )
                inner.append(aligned)

            widget.pos = (
                self.pos[0] + padding + total_offset + error,
                self.pos[1] + (1 if type(widget).__name__ == "Container" else 0),
            )

            if aligned is not None:
                total_offset += real_length(aligned) + separator_length

            vertical_lines.append(inner)
            self.mouse_targets += widget.mouse_targets

        lines = []
        for horizontal in zip_longest(*vertical_lines, fillvalue=" " * target_width):
            lines.append((reset() + separator).join(horizontal))

        for target in self.mouse_targets:
            target.adjust()

        return lines

    def debug(self) -> str:
        """Return identifiable information"""

        return super().debug().replace("Container", "Splitter", 1)


class InputField(Label):
    """An element to display user input

    This class does NOT read input. To use this widget, send it
    user data gathered by `pytermgui.input.getch` or other means.

    Example of usage:

    ```python3
    import pytermgui as ptg

    field = ptg.InputField()

    root = ptg.Container(
        "[210 bold]This is an InputField!",
        field,
    )

    while True:
        key = getch()

        # Send key to field
        field.handle_key(key)
        root.print()
    ```
    """

    styles = {
        "value": styles.FOREGROUND,
        "cursor": styles.MarkupFormatter("[inverse]{item}"),
        "fill": styles.MarkupFormatter("[@243]{item}"),
    }

    is_bindable = True

    def __init__(self, value: str = "", prompt: str = "", **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(prompt + value, **attrs)

        self.parent_align = WidgetAlignment.LEFT

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

        cursor_style = self._get_style("cursor")
        fill_style = self._get_style("fill")

        # Cache value to be reset later
        old = self.value

        # Create sides separated by cursor
        left = fill_style(self.value[: self.cursor])
        right = fill_style(self.value[self.cursor + 1 :])

        # Assign cursor character
        if self.selected_index is None:
            if len(self.value) <= self.cursor:
                cursor_char = ""

            else:
                cursor_char = fill_style(self.value[self.cursor])

        elif len(self.value) > self.cursor:
            cursor_char = cursor_style(self.value[self.cursor])

        else:
            cursor_char = cursor_style(" ")

        # Set new value, get lines using it
        self.value = self.prompt

        if len(self.prompt) > 0:
            self.value += " "

        self.value += left + cursor_char + right

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
    """

    locked: bool
    """Disallow mouse input, hide cursor and lock current state"""

    show_percentage: bool
    """Show percentage next to the bar"""

    chars = {"endpoint": "", "cursor": "█", "fill": "█", "rail": "─"}

    styles = {
        "filled": styles.CLICKABLE,
        "unfilled": styles.FOREGROUND,
        "cursor": styles.CLICKABLE,
        "highlight": styles.CLICKED,
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
        rail_char = self._get_char("rail")
        assert isinstance(rail_char, str)

        endpoint_char = self._get_char("endpoint")
        assert isinstance(endpoint_char, str)

        cursor_char = self._get_char("cursor")
        assert isinstance(cursor_char, str)

        fill_char = self._get_char("fill")
        assert isinstance(fill_char, str)

        # Clamp value
        self._display_value = max(
            0, min(self._display_value, self.width, self._available)
        )

        # Only show cursor if not locked
        if self.locked:
            cursor_char = ""

        # Only highlight cursor if currently selected
        if self.selected_index != 0:
            highlight_style = self._get_style("highlight")
            cursor_char = highlight_style(cursor_char)
            fill_char = highlight_style(fill_char)

        # Construct left side
        left = (self._display_value - real_length(cursor_char) + 1) * fill_char
        left = self._get_style("filled")(left) + cursor_char

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

        return [left + line_length * rail_char + endpoint_char + counter]
