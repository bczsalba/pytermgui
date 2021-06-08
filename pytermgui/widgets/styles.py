"""
pytermgui.widgets.styles
------------------------
author: bczsalba


This submodule provides the basic style methods for Widgets
"""

# pylint: disable=unused-argument

from dataclasses import dataclass
from typing import Callable, Union
from ..parser import markup_to_ansi
from ..ansi_interface import background

__all__ = [
    "MarkupFormatter",
    "StyleCall",
    "StyleType",
    "DepthlessStyleType",
    "CharType",
    "default_foreground",
    "default_background",
    "overrideable_style",
    "apply_markup",
]

StyleType = Callable[[int, str], str]
DepthlessStyleType = Callable[[str], str]
CharType = Union[str, list[str]]


@dataclass
class StyleCall:
    """A callable object that simplifies calling style methods"""

    # Widget cannot be imported into this module
    obj: "Widget"  # type: ignore
    method: StyleType

    def __call__(self, item: str) -> str:
        """DepthlessStyleType: Apply style method to item, using depth"""

        try:
            # this is seen as passing self as an argument, and
            # annotating it a staticmethod (which it functionally is)
            # does not fix the issue.
            return self.method(self.obj.depth, item)  # type: ignore

        # this is purposefully broad, as anything can happen during these calls.
        except Exception as error:
            raise RuntimeError(
                # this method isn't even called, so not really sure why it gets
                # invalid self argument.
                f'Could not apply style {self.method} to "{item}": {error}'  # type: ignore
            ) from error


@dataclass
class MarkupFormatter:
    """A style-factory that formats depth & item into the given markup on call"""

    markup: str
    ensure_reset: bool = True

    def __call__(self, depth: int, item: str) -> str:
        """StyleType: Format depth & item into given markup template"""

        return markup_to_ansi(
            self.markup.format(depth=depth, item=item), self.ensure_reset
        )


def default_foreground(depth: int, item: str) -> str:
    """StyleType: Default foreground style"""

    return item


def default_background(depth: int, item: str) -> str:
    """StyleType: Default background style"""

    return background(item, 30 + depth)


def overrideable_style(depth: int, item: str) -> str:
    """StyleType: A style method that is meant to be overwritten,
    to use in optional values."""

    return (
        "This method is not meant to be called, only use"
        + " it for setting and checking optional style fields."
    )


def apply_markup(depth: int, item: str) -> str:
    """StyleType: A style that parses markup `item` into ansi"""

    return markup_to_ansi(item, ensure_optimized=True, ensure_reset=False)
