"""
Conveniences for styling widgets

All styles have a `depth` and `item` argument. `depth` is an int
that represents that "deep" the Widget is within the hierarchy, and
`item` is the string that the style is applied to.
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
    """A callable object that simplifies calling style methods.

    Instances of this class are created within the `Widget._get_style`
    method, and this class should not be used outside of that context."""

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
    """A style-factory that formats depth & item into the given markup on call.

    Useful in Widget styles, such as:

    ```python3
    import pytermgui as ptg

    root = ptg.Container()

    # Set border style to be reactive to the widget's depth
    root.set_style("border", ptg.MarkupFactory("[35 @{depth}]{item}]")
    ```
    """

    markup: str
    ensure_reset: bool = True
    ensure_strip: bool = False

    def __call__(self, depth: int, item: str) -> str:
        """StyleType: Format depth & item into given markup template"""

        if self.ensure_strip:
            item = strip_ansi(item)

        return markup.parse(self.markup.format(depth=depth, item=item))


CLICKABLE = MarkupFormatter("[@238 72 bold]{item}")
"""Style for inactive clickable things, such as `pytermgui.widgets.Button`"""

CLICKED = MarkupFormatter("[238 @72 bold]{item}")
"""Style for active clickable things, such as `pytermgui.widgets.Button`"""

FOREGROUND = lambda depth, item: item
"""Standard foreground style, currently unused by the library"""

BACKGROUND = lambda depth, item: item
"""Standard background, used by most `fill` styles"""

MARKUP = lambda depth, item: markup.parse(item)
"""Style that parses value as markup. Used by most text labels, like `pytermgui.widgets.Label`"""
