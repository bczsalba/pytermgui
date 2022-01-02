"""
Mouse interactable widgets for simple button behaviours.
"""

from __future__ import annotations

# Some of these classes need to have more than 7 instance attributes.
# pylint: disable=too-many-instance-attributes

from typing import Optional, Any, Callable

from .base import Widget, MouseCallback, MouseTarget

from ..parser import markup
from ..helpers import real_length
from ..ansi_interface import MouseAction, MouseEvent

from . import styles as w_styles

__all__ = ["Button", "Checkbox", "Toggle"]


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
        onclick: Optional[MouseCallback] = None,
        padding: int = 0,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.label = label
        self.onclick = onclick
        self.padding = padding
        self._selectables_length = 1

    def handle_mouse(
        self, event: MouseEvent, target: MouseTarget | None = None
    ) -> bool:
        """Handle a mouse event"""

        mouse_action, position = event
        mouse_target = target or self.get_target(position)

        if mouse_action == MouseAction.LEFT_CLICK:
            self.selected_index = 0
            if mouse_target is not None:
                mouse_target.click(self)
                return True

        if mouse_action == MouseAction.RELEASE:
            self.selected_index = None
            return False

        return super().handle_mouse(event, mouse_target)

    def get_lines(self) -> list[str]:
        """Get object lines"""

        self.mouse_targets = []
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

        self.define_mouse_target(
            left=self.padding, right=-self.padding, height=1
        ).onclick = self.onclick

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
