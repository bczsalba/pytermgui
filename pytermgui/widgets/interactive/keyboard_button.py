"""This module provides a keyboard-accessible button."""

from __future__ import annotations

from typing import Callable, Any

from ...input import keys
from .button import Button


class KeyboardButton(Button):
    """A button with keyboard mnemonics in mind.

    Shoutout to the HackerNews thread where this was originally suggested:
        https://news.ycombinator.com/item?id=30517299#30533444
    """

    chars = {**Button.chars, **{"bracket": ["(", ")"]}}

    is_bindable = True

    def __init__(
        self,
        label: str,
        onclick: Callable[[Button], Any],
        index: int = 0,
        bound: str | None = None,
    ) -> None:
        """Initializes a KeyboardButton.

        For example, `KeyboardButton("Help")` will look like: "[ (H)elp ]", and
        `KeyboardButton("Test", index=1)` will give "[ T(e)st ]"

        Args:
            label: The label of the button.
            char: The "highlighted" character inside the label. Defaults to first
                character of the label.
            bound: The keybind that activates this button. Defaults to CTRL_{char}
                is used as the default binding.
        """

        if bound is None:
            bound = getattr(keys, "CTRL_" + label[index].upper())

        brackets = "{}".join(self._get_char("bracket"))
        label = label[:index] + brackets.format(label[index]) + label[index + 1 :]

        super().__init__(label, onclick)
        self.bind(bound, onclick)
