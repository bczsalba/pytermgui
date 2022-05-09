"""The Collapsible widget type."""

from __future__ import annotations

from typing import Any

from ..input import keys
from ..enums import Overflow
from .interactive import Toggle
from .containers import Container


__all__ = ["Collapsible"]


class Collapsible(Container):
    """A collapsible section of UI."""

    is_bindable = True

    def __init__(
        self, label: str, *items: Any, keyboard: bool = False, **attrs: Any
    ) -> None:
        """Initializes the widget.

        Args:
            label: The label for the trigger toggle.
            *items: The items that will be hidden when the object is collapsed.
            keyboard: If set, the first character of the label will be used as
                a `CTRL_` binding to toggle the object.
        """

        if keyboard:
            bind = label[0]
            self.trigger = Toggle(
                (f"▶ ({bind}){label[1:]}", f"▼ ({bind}){label[1:]}"),
                lambda *_: self.toggle(),
            )
        else:
            self.trigger = Toggle(
                (f"▶ {label}", f"▼ {label}"), lambda *_: self.toggle()
            )

        super().__init__(self.trigger, *items, box="EMPTY", **attrs)

        if keyboard:
            self.bind(
                getattr(keys, f"CTRL_{bind}"),
                lambda *_: self.trigger.toggle(),
                "Open dropdown",
            )

        self.collapsed_height = 1
        self.overflow = Overflow.HIDE
        self.height = self.collapsed_height

        self._is_expanded = False

    def toggle(self) -> Collapsible:
        """Toggles expanded state.

        Returns:
            This object.
        """

        if self.trigger.checked != self._is_expanded:
            self.trigger.toggle(run_callback=False)

        self._is_expanded = not self._is_expanded

        if self._is_expanded:
            self.overflow = Overflow.RESIZE
        else:
            self.overflow = Overflow.HIDE
            self.height = self.collapsed_height

        return self

    def collapse(self) -> Collapsible:
        """Collapses the dropdown.

        Does nothing if already collapsed.

        Returns:
            This object.
        """

        if self._is_expanded:
            self.toggle()

        return self

    def expand(self) -> Collapsible:
        """Expands the dropdown.

        Does nothing if already expanded.

        Returns:
            This object.
        """

        if not self._is_expanded:
            self.toggle()

        return self
