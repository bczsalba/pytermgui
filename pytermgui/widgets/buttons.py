"""
pytermgui.widget.buttons
------------------------
author: bczsalba


This submodule contains all of the button-related widgets.

These all have mouse_targets set, so are clickable. Most have `onclick`
callbacks.
"""

# Some of these classes need to have more than 7 instance attributes.
# pylint: disable=too-many-instance-attributes

from typing import Optional, Any, Callable

from .styles import StyleType, CharType, MarkupFormatter
from .base import Widget, MouseCallback, Container, MouseTarget

from ..parser import ansi
from ..helpers import real_length

__all__ = ["Button", "Checkbox", "Toggle", "Dropdown"]


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

        word = ansi(left + self.label + right, silence_exception=True)
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

    chars = Button.chars | {"delimiter": ["[", "]"], "checked": "X", "unchecked": " "}

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

    chars = Checkbox.chars | {"delimiter": [" ", " "], "checked": "choose"}

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


class Dropdown(Container):
    """A dropdown menu"""

    # TODO: Add Widget support for overlaying lines

    chars = Container.chars | {"default_value": "Choose an item"}
    styles = Container.styles | {"item": Button("").get_style("label").method}

    def __init__(
        self, items: list[str], callback: Callable[[str], Any], **attrs: Any
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)
        self.trigger = Checkbox(lambda *_: self.print(), parent_align=self.parent_align)
        self._update_label(items[0])
        self._add_widget(self.trigger)

        self.items = items
        self.callback = callback
        self.selected_index = 0

        self.width = max(len(item) for item in self.items)

        self.set_char("border", [""] * 4)
        self._item_buttons: list[Button] = []

    def _update_label(self, new: str) -> None:
        """Update label of trigger button"""

        self.trigger.set_char("checked", new)
        self.trigger.set_char("unchecked", new)
        self.trigger.label = new

    def _item_callback(self, _: MouseTarget, widget: Widget) -> None:
        """Callback assigned to all item buttons"""

        self.trigger.toggle()
        self._update_label(widget.label)

        if self.callback is not None:
            self.callback(widget.label)

    def get_lines(self) -> list[str]:
        """Get lines depending on state"""

        self._widgets = [self.trigger]
        self._item_buttons = []

        if self.trigger.checked:
            for item in self.items:
                button = Button(
                    item, onclick=self._item_callback, parent_align=self.parent_align
                )
                button.set_style("label", self.get_style("item").method)

                if item == self.trigger.label:
                    button.select(0)

                self._add_widget(button, run_get_lines=False)
                self._item_buttons.append(button)

        return super().get_lines()
