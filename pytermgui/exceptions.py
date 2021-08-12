"""
pytermgui.exceptions
--------------------
author: bczsalba


This module stores the custom Exception-s used in this module.
"""

from dataclasses import dataclass

__all__ = [
    "WidthExceededError",
    "LineLengthError",
    "MarkupSyntaxError",
]


class WidthExceededError(Exception):
    """Raised when an element's width is larger than the screen"""


class LineLengthError(Exception):
    """Raised when a widget line is too long or short"""


@dataclass
class MarkupSyntaxError(Exception):
    """Raised when parsed markup contains an error"""

    tag: str
    cause: str
    context: str

    @property
    def message(self) -> str:
        """Create message from tag, context and cause"""

        escaped_context = ascii(self.context).strip("'")
        return f'Tag "[{self.tag}]" in string "{escaped_context}" {self.cause}.'

    def escape_message(self) -> str:
        """Return message with markup tags escaped."""

        return self.message.replace("[", r"\[")
