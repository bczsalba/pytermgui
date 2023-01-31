"""
Conveniences for styling widgets

All styles have a `depth` and `item` argument. `depth` is an int
that represents that "deep" the Widget is within the hierarchy, and
`item` is the string that the style is applied to.
"""

# pylint: disable=unused-argument, too-many-instance-attributes
# pylint: disable=unnecessary-lambda-assignment

from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, List, Type, Union

from ..highlighters import Highlighter
from ..markup import Token, get_markup, tim, tokenize_markup
from ..markup.parsing import _sub_aliases
from ..regex import RE_MARKUP, strip_ansi

__all__ = [
    "MarkupFormatter",
    "HighlighterStyle",
    "StyleCall",
    "StyleType",
    "StyleManager",
    "DepthlessStyleType",
    "CharType",
]

if TYPE_CHECKING:
    from .base import Widget

StyleType = Callable[[int, str], str]
DepthlessStyleType = Callable[[str], str]
CharType = Union[List[str], str]

StyleValue = Union[str, "MarkupFormatter", "HighlighterStyle", "StyleCall", StyleType]


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
                f"Could not apply style {self.method} to {item!r}: {error}"  # type: ignore
            ) from error

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False

        return other.method == self.method


@dataclass
class MarkupFormatter:
    """A style that formats depth & item into the given markup on call.

    Useful in Widget styles, such as:

    ```python3
    import pytermgui as ptg

    root = ptg.Container()

    # Set border style to be reactive to the widget's depth
    root.set_style("border", ptg.MarkupFactory("[35 @{depth}]{item}]")
    ```
    """

    markup: str
    ensure_strip: bool = False

    _markup_cache: dict[str, str] = field(init=False, default_factory=dict)

    def __call__(self, depth: int, item: str) -> str:
        """StyleType: Format depth & item into given markup template"""

        if self.ensure_strip:
            item = strip_ansi(item)

        if item in self._markup_cache:
            item = self._markup_cache[item]

        else:
            original = item
            item = get_markup(item)
            self._markup_cache[original] = item

        return tim.parse(self.markup.format(depth=depth, item=item))

    def __str__(self) -> str:
        """Returns __repr__, but with markup escaped."""

        return self.__repr__().replace("[", r"\[")


@dataclass
class HighlighterStyle:
    """A style that highlights the items given to it.

    See `pytermgui.highlighters` for more information.
    """

    highlighter: Highlighter

    def __call__(self, _: int, item: str) -> str:
        """Highlights the given string."""

        return tim.parse(self.highlighter(item))


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
        **base,
    ) -> None:

        """Initializes a `StyleManager`.

        Args:
            parent: The parent of this instance. It will be assigned in all
                `StyleCall`-s created by it.
        """

        self.__dict__["_is_setup"] = False

        self.parent = parent

        super().__init__()

        for key, value in base.items():
            self._set_as_stylecall(key, value)

        self.__dict__["_is_setup"] = self.parent is not None

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

        tokens = _sub_aliases(list(tokenize_markup(f"[{shorthand}]")), tim.context)

        colors = [tkn for tkn in tokens if Token.is_color(tkn)]

        if any(tkn.color.background for tkn in colors) and not any(
            not tkn.color.background for tkn in colors
        ):
            shorthand += " #auto"

        markup = f"[{shorthand}]"

        if not "{item}" in shorthand:
            markup += "{item}"

        return MarkupFormatter(markup)

    @classmethod
    def merge(cls, other: StyleManager, **styles: str) -> StyleManager:
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

        return cls(**{**other, **styles})

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

        return type(self)(parent, **self.data)

    def _set_as_stylecall(self, key: str, item: StyleValue) -> None:
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

    def __setitem__(self, key: str, value: StyleValue) -> None:
        """Sets an item in `self.data`.

        If the item is a string, it will be expanded into a `MarkupFormatter` before
        being converted into the `StyleCall`, using `expand_shorthand`.
        """

        self._set_as_stylecall(key, value)

    def __setattr__(self, key: str, value: StyleValue) -> None:
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

        if self.__dict__.get("_is_setup") and key not in self.__dict__:
            raise KeyError(f"Style {key!r} was not defined during construction.")

        self.__dict__[key] = value

    def __getattr__(self, key: str) -> StyleCall:
        """Allows styles.dot_syntax."""

        if key in self.__dict__:
            return self.__dict__[key]

        if key in self.__dict__["data"]:
            return self.__dict__["data"][key]

        raise AttributeError(key, self.data)

    def __call__(self, **styles: StyleValue) -> Any:
        """Allows calling the manager and setting its styles.

        For example:
        ```
        >>> Button("Hello").styles(label="@60")
        ```
        """

        for key, value in styles.items():
            self._set_as_stylecall(key, value)

        return self.parent
