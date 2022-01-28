"""The module housing the various interactive Widget types."""

# These widgets have more than the 7 allowed instance attributes.
# pylint: disable=too-many-instance-attributes

from __future__ import annotations

import string
from typing import Any, Callable, Optional

from ..ansi_interface import MouseAction, MouseEvent
from ..enums import HorizontalAlignment
from ..helpers import real_length
from ..input import keys
from ..parser import markup
from . import styles as w_styles
from .base import Label, Widget


class Button(Widget):
    """A simple Widget representing a mouse-clickable button"""

    chars: dict[str, w_styles.CharType] = {"delimiter": ["  ", "  "]}

    styles: dict[str, w_styles.StyleType] = {
        "label": w_styles.CLICKABLE,
        "highlight": w_styles.CLICKED,
    }

    def __init__(
        self,
        label: str = "Button",
        onclick: Optional[Callable[[Button], Any]] = None,
        padding: int = 0,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.label = label
        self.onclick = onclick
        self.padding = padding
        self._selectables_length = 1

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handle a mouse event"""

        if event.action == MouseAction.LEFT_CLICK:
            self.selected_index = 0
            if self.onclick is not None:
                self.onclick(self)

            return True

        if event.action == MouseAction.RELEASE:
            self.selected_index = None
            return True

        return super().handle_mouse(event)

    def handle_key(self, key: str) -> bool:
        """Handles a keypress"""

        if key == keys.RETURN and self.onclick is not None:
            self.onclick(self)
            return True

        return False

    def get_lines(self) -> list[str]:
        """Get object lines"""

        label_style = self._get_style("label")
        delimiters = self._get_char("delimiter")
        highlight_style = self._get_style("highlight")

        assert isinstance(delimiters, list) and len(delimiters) == 2
        left, right = delimiters

        word = markup.parse(left + self.label + right)
        if self.selected_index is None:
            word = label_style(word)
        else:
            word = highlight_style(word)

        line = self.padding * " " + word
        self.width = real_length(line)

        return [line]


# TODO: Rewrite this to also have a label
class Checkbox(Button):
    """A simple checkbox"""

    chars = {
        **Button.chars,
        **{"delimiter": ["[", "]"], "checked": "X", "unchecked": " "},
    }

    def __init__(
        self,
        callback: Callable[[Any], Any] | None = None,
        checked: bool = False,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        unchecked = self._get_char("unchecked")
        assert isinstance(unchecked, str)

        super().__init__(unchecked, onclick=self.toggle, **attrs)

        self.callback = None
        self.checked = False
        if self.checked != checked:
            self.toggle(run_callback=False)

        self.callback = callback

    def _run_callback(self) -> None:
        """Run the checkbox callback with the new checked flag as its argument"""

        if self.callback is not None:
            self.callback(self.checked)

    def toggle(self, *_: Any, run_callback: bool = True) -> None:
        """Toggle state"""

        chars = self._get_char("checked"), self._get_char("unchecked")
        assert isinstance(chars[0], str) and isinstance(chars[1], str)

        self.checked ^= True
        if self.checked:
            self.label = chars[0]
        else:
            self.label = chars[1]

        self.get_lines()

        if run_callback:
            self._run_callback()


class Toggle(Checkbox):
    """A specialized checkbox showing either of two states"""

    chars = {**Checkbox.chars, **{"delimiter": [" ", " "], "checked": "choose"}}

    def __init__(
        self,
        states: tuple[str, str],
        callback: Callable[[str], Any] | None = None,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        self.set_char("checked", states[0])
        self.set_char("unchecked", states[1])

        super().__init__(callback, **attrs)
        self.toggle(run_callback=False)

    def _run_callback(self) -> None:
        """Run the toggle callback with the label as its argument"""

        if self.callback is not None:
            self.callback(self.label)


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

        self.width += 2
        lines = super().get_lines()

        # Set old value
        self.value = old
        self.width -= 2

        return [
            line + fill_style((self.width - real_length(line) - 1) * " ")
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
        "filled": w_styles.CLICKABLE,
        "unfilled": w_styles.FOREGROUND,
        "cursor": w_styles.CLICKABLE,
        "highlight": w_styles.CLICKED,
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

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Change slider position"""

        # Disallow changing state when Slider is locked
        if not self.locked:
            if event.action is MouseAction.RELEASE:
                self.selected_index = None
                return True

            if event.action in [MouseAction.LEFT_DRAG, MouseAction.LEFT_CLICK]:
                self._display_value = max(
                    0, min(event.position[0] - self.pos[0] + 1, self._available)
                )
                self.selected_index = 0

                if self.onchange is not None:
                    self.onchange(self.value)

                return True

        return super().handle_mouse(event)

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

        # Get counter string
        counter = ""
        if self.show_counter:
            percentage = (self._display_value * 100) // self._available
            counter = f"{str(percentage) + '%': >5}"

        # Construct final string
        self._available = self.width - len(counter) - real_length(endpoint_char)
        line_length = self._available - self._display_value

        return [left + line_length * rail_char + endpoint_char + counter]
