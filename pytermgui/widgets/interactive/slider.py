"""This module contains the `Slider` class."""

from __future__ import annotations
from typing import Any, Callable

from ...ansi_interface import MouseAction, MouseEvent
from ...input import keys
from ...helpers import real_length
from .. import styles as w_styles
from ..base import Widget


class Slider(Widget):  # pylint: disable=too-many-instance-attributes
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
