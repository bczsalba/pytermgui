"""
pytermgui.widget.buttons
------------------------
author: bczsalba


This submodule contains all of the button-related widgets.

These all have mouse_targets set, so are clickable. Most have `onclick`
callbacks.
"""

from __future__ import annotations

# Some of these classes need to have more than 7 instance attributes.
# pylint: disable=too-many-instance-attributes

from typing import Optional, Any, Callable

from .styles import StyleType, CharType, MarkupFormatter
from .base import Widget, MouseCallback

from ..parser import markup
from ..helpers import real_length

__all__ = ["Button", "Checkbox", "Toggle"]


class Button(Widget):
    """A visual MouseTarget"""

    chars: dict[str, CharType] = {"delimiter": ["  ", "  "]}

    styles: dict[str, StyleType] = {
        "label": MarkupFormatter("[72 @238 bold]{item}"),
        "highlight": MarkupFormatter("[238 @72 bold]{item}"),
    }

    def __init__(
        self,
        label: str,
        onclick: Optional[MouseCallback] = None,
        padding: int = 0,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.label = label
        self._selectables_length = 1
        self.is_selectable = True
        self.onclick = onclick
        self.padding = padding

    def get_lines(self) -> list[str]:
        """Get object lines"""

        self.mouse_targets = []
        label_style = self.get_style("label")
        delimiters = self.get_char("delimiter")
        highlight_style = self.get_style("highlight")

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
        self.forced_width = real_length(word)

        return [self.padding * " " + word]


class Checkbox(Button):
    """A simple checkbox"""

    chars = {
        **Button.chars,
        **{"delimiter": ["[", "]"], "checked": "X", "unchecked": " "},
    }

    def __init__(
        self, callback: Callable[[Any], Any], checked: bool = False, **attrs: Any
    ) -> None:
        """Initialize object"""

        unchecked = self.get_char("unchecked")
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

        chars = self.get_char("checked"), self.get_char("unchecked")
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
        self, states: tuple[str, str], callback: Callable[[str], Any], **attrs: Any
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
