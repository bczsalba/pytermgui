"""This module contains the `InputField` class."""

from __future__ import annotations
from typing import Any

import string

from ...ansi_interface import MouseAction, MouseEvent
from ...input import keys
from ...enums import HorizontalAlignment
from ...helpers import real_length
from .. import styles as w_styles
from ..base import Label


class InputField(Label):
    """An element to display user input

    This class does NOT read input. To use this widget, send it
    user data gathered by `pytermgui.input.getch` or other means.

    Args:
        value: The default value of this InputField.
        prompt: Text to display to the left of the field.
        expect: Type object that all input should match. This type
              is called on each new key, and if a `ValueError` is
              raised the key is discarded. The `value` attribute
              is also converted using this type.

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
        "value": w_styles.FOREGROUND,
        "cursor": w_styles.MarkupFormatter("[inverse]{item}"),
        "fill": w_styles.MarkupFormatter("[@243]{item}"),
    }

    is_bindable = True

    def __init__(
        self,
        value: str = "",
        prompt: str = "",
        expect: type | None = None,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(prompt + value, **attrs)

        self.parent_align = HorizontalAlignment.LEFT

        self.value = value
        self.prompt = prompt
        self.cursor = real_length(self.value)
        self.expect = expect

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

        self._cursor = max(0, min(value, real_length(str(self.value))))

    def handle_key(self, key: str) -> bool:
        """Handle keypress, return True if success, False if failure"""

        def _run_callback() -> None:
            """Call callback if `keys.ANY_KEY` is bound"""

            if keys.ANY_KEY in self._bindings:
                method, _ = self._bindings[keys.ANY_KEY]
                method(self, key)

        if self.execute_binding(key):
            return True

        if key == keys.TAB:
            return False

        if key == keys.BACKSPACE and self.cursor > 0:
            self.value = str(self.value)
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
            if self.expect is not None:
                try:
                    self.expect(key)
                except ValueError:
                    return False

            self.value = str(self.value)

            left = self.value[: self.cursor] + key
            right = self.value[self.cursor :]

            self.value = left + right
            self.cursor += len(key)
            _run_callback()

        if self.expect is not None and self.value != "":
            self.value = self.expect(self.value)

        return True

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handle mouse events"""

        # Ignore mouse release events
        if event.action is MouseAction.RELEASE:
            return True

        # Set cursor to mouse location
        if event.action is MouseAction.LEFT_CLICK:
            self.cursor = event.position[0] - self.pos[0]
            return True

        return super().handle_mouse(event)

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        cursor_style = self._get_style("cursor")
        fill_style = self._get_style("fill")

        # Cache value to be reset later
        old = self.value

        # Stringify value in case `expect` is set
        self.value = str(self.value)

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

        lines = super().get_lines()

        # Set old value
        self.value = old

        return [
            line + fill_style((self.width - real_length(line)) * " ") for line in lines
        ]
