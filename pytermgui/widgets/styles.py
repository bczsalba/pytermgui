"""
Conveniences for styling widgets

All styles have a `depth` and `item` argument. `depth` is an int
that represents that "deep" the Widget is within the hierarchy, and
`item` is the string that the style is applied to.
"""

# pylint: disable=unused-argument

from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass
from typing import Callable, Union, List, Type, TYPE_CHECKING

from ..helpers import strip_ansi
from ..parser import tim, RE_MARKUP

__all__ = [
    "MarkupFormatter",
    "StyleCall",
    "StyleType",
    "StyleManager",
    "DepthlessStyleType",
    "CharType",
    "MARKUP",
    "FOREGROUND",
    "BACKGROUND",
    "CLICKABLE",
    "CLICKED",
]

if TYPE_CHECKING:
    from .base import Widget

StyleType = Callable[[int, str], str]
DepthlessStyleType = Callable[[str], str]
CharType = Union[List[str], str]


@dataclass
class StyleCall:
    """A callable object that simplifies calling style methods.

    Instances of this class are created within the `Widget._get_style`
    method, and this class should not be used outside of that context."""

    obj: Widget | Type[Widget] | None
    method: StyleType

    def __call__(self, item: str) -> str:
        """DepthlessStyleType: Apply style method to item, using depth"""

        if self.obj is None:
            raise ValueError(
                f"Can not call {self.method!r}, as no object is assigned to this StyleCall."
            )

        try:
            # mypy fails on one machine with this, but not on the other.
            return self.method(self.obj.depth, item)  # type: ignore

        # this is purposefully broad, as anything can happen during these calls.
        except Exception as error:
            raise RuntimeError(
                f'Could not apply style {self.method} to "{item}": {error}'  # type: ignore
            ) from error

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False

        return other.method == self.method


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

        return tim.parse(self.markup.format(depth=depth, item=item))

    def __str__(self) -> str:
        """Returns __repr__, but with markup escaped."""

        return self.__repr__().replace("[", r"\[")


# There is only a single ancestor here.
class StyleManager(UserDict):  # pylint: disable=too-many-ancestors
    """An fancy dictionary to manage a Widget's styles.

    Individual styles can be accessed two ways:

    ```python3
    manager.styles.style_name == manager._get_style("style_name")
    ```

    Same with setting:

    ```python3
    widget.styles.style_name = ...
    widget.set_style("style_name", ...)
    ```

    The `set` and `get` methods remain for backwards compatibility reasons, but all
    newly written code should use the dot syntax.

    It is also possible to set styles as markup shorthands. For example:

    ```python3
    widget.styles.border = "60 bold"
    ```

    ...is equivalent to:

    ```python3
    widget.styles.border = "[60 bold]{item}"
    ```
    """

    def __init__(
        self,
        parent: Widget | Type[Widget] | None = None,
        late_base: StyleManager | None = None,
        **base,
    ) -> None:

        """Initializes a `StyleManager`.

        Args:
            parent: The parent of this instance. It will be assigned in all
                `StyleCall`-s created by it.
            late_base: Additional data that will be added to this manager on `branch`.
        """

        self.parent = parent
        super().__init__()

        for key, value in base.items():
            self._set_as_stylecall(key, value)

        self._late_base = late_base

    @staticmethod
    def expand_shorthand(shorthand: str) -> MarkupFormatter:
        """Expands a shorthand string into a `MarkupFormatter` instance.

        For example, all of these will expand into `MarkupFormatter([60]{item}')`:
        - '60'
        - '[60]'
        - '[60]{item}'

        Args:
            shorthand: The short version of markup to expand.

        Returns:
            A `MarkupFormatter` with the expanded markup.
        """

        if len(shorthand) == 0:
            return MarkupFormatter("{item}")

        if RE_MARKUP.match(shorthand) is not None:
            return MarkupFormatter(shorthand)

        markup = "[" + shorthand + "]"

        if not "{item}" in shorthand:
            markup += "{item}"

        return MarkupFormatter(markup)

    @classmethod
    def merge(cls, other: StyleManager, **styles) -> StyleManager:
        """Creates a new manager that merges `other` with the passed in styles.

        Args:
            other: The style manager to base the new one from.
            **styles: The additional styles the new instance should have.

        Returns:
            A new `StyleManager`. This instance will only gather its data when
            `branch` is called on it. This is done so any changes made to the original
            data between the `merge` call and the actual usage of the instance will be
            reflected.
        """

        return cls(late_base=other, **styles)

    def branch(self, parent: Widget | Type[Widget]) -> StyleManager:
        """Branch off from the `base` style dictionary.

        This method should be called during widget construction. It creates a new
        `StyleManager` based on self, but with its data detached from the original.

        Args:
            parent: The parent of the new instance.

        Returns:
            A new `StyleManager`, with detached instances of data. This can then be
            modified without touching the original instance.
        """

        return type(self)(parent, **{**self.data, **(self._late_base or {})})

    def _set_as_stylecall(
        self, key: str, item: str | StyleCall | MarkupFormatter | StyleType
    ) -> None:
        """Sets `self.data[key]` as a `StyleCall` of the given item.

        If the item is a string, it will be expanded into a `MarkupFormatter` before
        being converted into the `StyleCall`, using `expand_shorthand`.
        """

        if isinstance(item, StyleCall):
            self.data[key] = StyleCall(self.parent, item.method)
            return

        if isinstance(item, str):
            item = self.expand_shorthand(item)

        self.data[key] = StyleCall(self.parent, item)

    def __setitem__(
        self, key: str, value: str | MarkupFormatter | StyleCall | StyleType
    ) -> None:
        """Sets an item in `self.data`.

        If the item is a string, it will be expanded into a `MarkupFormatter` before
        being converted into the `StyleCall`, using `expand_shorthand`.
        """

        self._set_as_stylecall(key, value)

    def __setattr__(
        self, key: str, value: str | MarkupFormatter | StyleCall | StyleType
    ) -> None:
        """Sets an attribute.

        It first looks if it can set inside self.data, and defaults back to
        self.__dict__.

        Raises:
            KeyError: The given key is not a defined attribute, and is not part of this
                object's style set.
        """

        found = False
        if "data" in self.__dict__:
            for part in key.split("__"):
                if part in self.data:
                    self._set_as_stylecall(part, value)
                    found = True

        if found:
            return

        if self.__dict__.get("_late_base") is not None and key not in self.__dict__:
            raise KeyError(f"Style {key!r} was not defined during construction.")

        self.__dict__[key] = value

    def __getattr__(self, key: str) -> StyleCall:
        """Allows styles.dot_syntax."""

        if key in self.__dict__:
            return self.__dict__[key]

        return self.__dict__["data"][key]


CLICKABLE = MarkupFormatter("[@238 72 bold]{item}")
"""Style for inactive clickable things, such as `pytermgui.widgets.Button`"""

CLICKED = MarkupFormatter("[238 @72 bold]{item}")
"""Style for active clickable things, such as `pytermgui.widgets.Button`"""

FOREGROUND = lambda depth, item: item
"""Standard foreground style, currently unused by the library"""

BACKGROUND = lambda depth, item: item
"""Standard background, used by most `fill` styles"""

MARKUP = lambda depth, item: tim.parse(item)
"""Style that parses value as markup. Used by most text labels, like `pytermgui.widgets.Label`"""
