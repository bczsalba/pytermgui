"""This module contains the `Checkbox` class."""

from __future__ import annotations

from typing import Any, Callable

from .button import Button


# TODO: Rewrite this to also have a label
class Checkbox(Button):
    """A simple checkbox"""

    chars = {
        **Button.chars,
        **{"delimiter": [" ", " "], "checked": "▣", "unchecked": "□"},
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
