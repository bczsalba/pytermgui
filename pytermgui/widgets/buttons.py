"""
pytermgui.widget.buttons
------------------------
author: bczsalba


This submodule contains all of the button-related widgets.

These all have mouse_targets set, so are clickable. Most have `onclick`
callbacks.
"""

from typing import Optional, Any, Callable

from .base import Widget, MouseCallback, Container
from .styles import StyleType, CharType, MarkupFormatter

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

        assert len(delimiters) == 2
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
        self, callback: Callable[[bool], Any], checked: bool = False, **attrs
    ) -> None:
        """Initialize object"""

        super().__init__(self.get_char("unchecked"), onclick=self.toggle, **attrs)

        self.callback = None
        self.checked = False
        if self.checked != checked:
            self.toggle()

        self.callback = callback

    def toggle(self, *_) -> None:
        """Toggle state"""

        self.checked ^= True
        if self.checked:
            self.label = self.get_char("checked")
        else:
            self.label = self.get_char("unchecked")

        self.get_lines()

        if self.callback is not None:
            self.callback(self.checked)


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
        self.toggle()


class Dropdown(Container):
    """A dropdown menu"""

    # TODO: Add Widget support for overlaying lines

    chars = Container.chars | {"default_value": "Choose an item"}
    styles = Container.styles | {"item": Button.get_style(Button, "label").method}

    def __init__(
        self, items: list[str], callback: Callable[[str], Any], **attrs
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

    def _item_callback(self, _, widget: Widget) -> None:
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
