"""This module contains the `Button` class."""


from __future__ import annotations

from typing import Any, Callable, Optional

from ..ansi_interface import MouseAction, MouseEvent
from ..input import keys
from . import styles as w_styles
from .base import Widget


class Button(Widget):
    """A simple Widget representing a mouse-clickable button"""

    styles = w_styles.StyleManager(
        label="@surface dim #auto",
        highlight="@surface+1 dim #auto",
        _current=None,
    )

    chars: dict[str, w_styles.CharType] = {"delimiter": ["  ", "  "]}

    def __init__(
        self,
        label: str = "Button",
        onclick: Optional[Callable[[Button], Any]] = None,
        padding: int = 0,
        centered: bool = False,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)
        self._selectables_length = 1

        if not any("width" in attr for attr in attrs):
            self.width = len(label)

        self.label = label
        self.onclick = onclick
        self.padding = padding
        self.centered = centered

        self.styles["_current"] = self.styles.label

    def on_hover(self, _) -> bool:
        """Sets highlight style when hovering."""

        self.styles["_current"] = self.styles.highlight
        return False

    def on_release(self, _) -> bool:
        """Sets normal style when no longer hovering."""

        self.styles["_current"] = self.styles.label
        return False

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handles a mouse event"""

        if super().handle_mouse(event):
            return True

        if event.action == MouseAction.LEFT_CLICK:
            self.selected_index = 0
            if self.onclick is not None:
                self.onclick(self)

            return True

        if event.action == MouseAction.RELEASE:
            self.selected_index = None
            return True

        return False

    def handle_key(self, key: str) -> bool:
        """Handles a keypress"""

        if key in (keys.RETURN, keys.CARRIAGE_RETURN) and self.onclick is not None:
            self.onclick(self)
            return True

        return False

    def get_lines(self) -> list[str]:
        """Get object lines"""

        delimiters = self._get_char("delimiter")
        assert isinstance(delimiters, list) and len(delimiters) == 2

        left, right = delimiters
        left = left.replace("[", r"\[")

        if self.selected_index is None:
            style = self.styles["_current"]
        else:
            style = self.styles.highlight

        line = style(left + self.label + right + self.padding * " ")

        return [line]
