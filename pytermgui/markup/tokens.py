from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Iterator, TypeVar

from ..colors import Color, str_to_color

__all__ = [
    "Token",
    "PlainToken",
    "StyleToken",
    "ColorToken",
    "AliasToken",
    "ClearToken",
    "MacroToken",
    "HLinkToken",
    "CursorToken",
]


class Token:
    value: str

    @property
    def markup(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and other.value == self.value

    def __repr__(self) -> str:
        return f"<{type(self).__name__} markup: '[{self.markup}]'>"

    def __fancy_repr__(self) -> str:
        yield f"<{type(self).__name__} markup: "
        yield {
            "text": f"[{self.markup}]{self.markup}[/{self.markup}]",
            "highlight": False,
        }
        yield ">"

    def is_plain(self) -> bool:
        return isinstance(self, PlainToken)

    def is_color(self) -> bool:
        return isinstance(self, ColorToken)

    def is_style(self) -> bool:
        return isinstance(self, StyleToken)

    def is_alias(self) -> bool:
        return isinstance(self, AliasToken)

    def is_macro(self) -> bool:
        return isinstance(self, MacroToken)

    def is_clear(self) -> bool:
        return isinstance(self, ClearToken)

    def is_hyperlink(self) -> bool:
        return isinstance(self, HLinkToken)

    def is_cursor(self) -> bool:
        return isinstance(self, CursorToken)


@dataclass(frozen=True, repr=False)
class PlainToken(Token):
    __slots__ = ("value",)

    value: str

    def __repr__(self) -> str:
        return f"<{type(self).__name__} markup: {self.markup!r}>"

    def __fancy_repr__(self) -> str:
        yield f"<{type(self).__name__} markup: {self.markup!r}>"


@dataclass(frozen=True, repr=False)
class ColorToken(Token):
    __slots__ = ("value",)

    value: str
    color: Color

    def __fancy_repr__(self) -> str:
        clearer = "bg" if self.color.background else "fg"

        yield f"<{type(self).__name__} markup: "
        yield {
            "text": f"[{self.markup}]{self.markup}[/{clearer}]",
            "highlight": False,
        }
        yield ">"

    @property
    def markup(self) -> str:
        return self.color.markup


@dataclass(frozen=True, repr=False)
class StyleToken(Token):
    __slots__ = ("value",)

    value: str


@dataclass(frozen=True, repr=False)
class ClearToken(Token):
    __slots__ = ("value",)

    value: str

    def __fancy_repr__(self) -> str:
        target = self.markup[1:]
        yield f"<{type(self).__name__} markup: "
        yield {
            "text": f"[210 strikethrough]/[/fg {target}]{target}[/{target} /]",
            "highlight": False,
        }
        yield ">"

    def targets(self, token: Token) -> bool:
        if token.is_clear():
            return False

        if self.value in ("/", f"/{token.value}"):
            return True

        if token.is_hyperlink() and self.value == "/~":
            return True

        if not token.is_color():
            return False

        if self.value == "/fg" and not token.color.background:
            return True

        return self.value == "/bg" and token.color.background


@dataclass(frozen=True, repr=False)
class AliasToken(Token):
    __slots__ = ("value",)

    value: str


@dataclass(frozen=True, repr=False)
class MacroToken(Token):
    __slots__ = ("value", "arguments")

    value: str
    arguments: tuple[str, ...]

    @property
    def markup(self) -> str:
        return f"{self.value}({':'.join(self.arguments)})"


@dataclass(frozen=True, repr=False)
class HLinkToken(Token):
    __slots__ = ("value",)

    value: str

    def __fancy_repr__(self) -> str:
        yield f"<{type(self).__name__} markup: "
        yield {
            "text": f"[{self.markup}]~[blue underline]{self.value}[/fg /underline /~]",
            "highlight": False,
        }
        yield ">"

    @property
    def markup(self) -> str:
        return f"~{self.value}"


@dataclass(frozen=True, repr=False)
class CursorToken(Token):
    __slots__ = ("value", "y", "x")

    value: str
    y: int | None
    x: int | None

    def __iter__(self) -> Iterator[int]:
        return iter((self.y, self.x))

    def __repr__(self) -> str:
        return f"<{type(self).__name__} position: {(';'.join(map(str, self)))}>"

    def __fancy_repr__(self) -> str:
        yield self.__repr__()

    @property
    def markup(self) -> str:
        return f"({self.value})"
