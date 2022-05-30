"""This module contains the `Toggle` class."""

from __future__ import annotations

from typing import Any, Callable

from .checkbox import Checkbox


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

        self.states = states

        self.set_char("checked", states[0])
        self.set_char("unchecked", states[1])

        super().__init__(callback, **attrs)
        self.toggle(run_callback=False)

    def _run_callback(self) -> None:
        """Run the toggle callback with the label as its argument"""

        if self.callback is not None:
            self.callback(self.label)
