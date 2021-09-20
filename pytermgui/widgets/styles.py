"""
pytermgui.widgets.styles
------------------------
author: bczsalba


This submodule provides the basic style methods for Widgets
"""

# pylint: disable=unused-argument

from dataclasses import dataclass
from typing import Callable, Union, List

from ..parser import markup
from ..helpers import strip_ansi

__all__ = [
    "MarkupFormatter",
    "StyleCall",
    "StyleType",
    "DepthlessStyleType",
    "CharType",
    "MARKUP",
    "FOREGROUND",
    "BACKGROUND",
    "CLICKABLE",
    "CLICKED",
]

StyleType = Callable[[int, str], str]
DepthlessStyleType = Callable[[str], str]
CharType = Union[List[str], str]


@dataclass
class StyleCall:
    """A callable object that simplifies calling style methods"""

    # Widget cannot be imported into this module
    obj: "Widget"  # type: ignore
    method: StyleType

    def __call__(self, item: str) -> str:
        """DepthlessStyleType: Apply style method to item, using depth"""

        try:
            # mypy fails on one machine with this, but not on the other.
            return self.method(self.obj.depth, item)  # type: ignore

        # this is purposefully broad, as anything can happen during these calls.
        except Exception as error:
            raise RuntimeError(
                f'Could not apply style {self.method} to "{item}": {error}'  # type: ignore
            ) from error


@dataclass
class MarkupFormatter:
    """A style-factory that formats depth & item into the given markup on call"""

    markup: str
    ensure_reset: bool = True
    ensure_strip: bool = False

    def __call__(self, depth: int, item: str) -> str:
        """StyleType: Format depth & item into given markup template"""

        if self.ensure_strip:
            item = strip_ansi(item)

        return markup.parse(self.markup.format(depth=depth, item=item))


CLICKABLE = MarkupFormatter("[@238 72 bold]{item}")
CLICKED = MarkupFormatter("[238 @72 bold]{item}")
FOREGROUND = lambda depth, item: item
BACKGROUND = lambda depth, item: item
MARKUP = lambda depth, item: markup.parse(item)
