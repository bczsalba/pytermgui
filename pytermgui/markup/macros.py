"""All PTG-builtin TIM macros."""

from __future__ import annotations

from random import shuffle
from typing import Any, TypeVar

from .parsing import parse

DEFAULT_MACROS = {}

MarkupLanguage = Any


MacroTemplate = TypeVar("MacroTemplate")


def export_macro(func: MacroTemplate) -> MacroTemplate:
    """A decorator to add a function to `DEFAULT_MACROS`."""

    name = "_".join(func.__name__.split("_")[1:])  # type: ignore

    DEFAULT_MACROS[f"!{name}"] = func

    return func


def apply_default_macros(lang: MarkupLanguage) -> None:
    """Applies all macros in `DEFAULT_MACROS`.

    Args:
        lang: The language to apply the macros to.
    """

    for name, value in DEFAULT_MACROS.items():
        lang.define(name, value)


@export_macro
def macro_upper(text: str) -> str:
    """Turns the text into uppercase."""

    return text.upper()


@export_macro
def macro_lower(text: str) -> str:
    """Turns the text into lowercase."""

    return text.lower()


@export_macro
def macro_title(text: str) -> str:
    """Turns the text into titlecase."""

    return text.title()


@export_macro
def macro_align(width: str, alignment: str, content: str) -> str:
    """Aligns given text using fstrings.

    Args:
        width: The width to align to.
        alignment: One of "left", "center", "right".
        content: The content to align; implicit argument.
    """

    aligner = "<" if alignment == "left" else (">" if alignment == "right" else "^")
    return f"{content:{aligner}{width}}"


@export_macro
def macro_expand(lang: MarkupLanguage, tag: str) -> str:
    """Expands a tag alias."""

    if not tag in lang.user_tags:
        return tag

    return lang.get_markup(f"\x1b[{lang.user_tags[tag]}m ")[:-1]


@export_macro
def macro_shuffle(item: str) -> str:
    """Shuffles a string using shuffle.shuffle on its list cast."""

    shuffled = list(item)
    shuffle(shuffled)

    return "".join(shuffled)


def _apply_colors(colors: list[str] | list[int], item: str) -> str:
    """Applies the given list of colors to the item, spread out evenly."""

    blocksize = max(round(len(item) / len(colors)), 1)

    out = ""
    current_block = 0
    for i, char in enumerate(item):
        if i % blocksize == 0 and current_block < len(colors):
            out += f"[{colors[current_block]}]"
            current_block += 1

        out += char

    return parse(out + "[/fg]", append_reset=False) + "\x1b[0m"


@export_macro
def macro_rainbow(item: str) -> str:
    """Creates rainbow-colored text."""

    colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]

    return _apply_colors(colors, item)


@export_macro
def macro_gradient(base_str: str, item: str) -> str:
    """Creates an xterm-256 gradient from a base color.

    This exploits the way the colors are arranged in the xterm color table; every
    36th color is the next item of a single gradient.

    The start of this given gradient is calculated by decreasing the given base by 36 on
    every iteration as long as the point is a valid gradient start.

    After that, the 6 colors of this gradient are calculated and applied.
    """

    if not base_str.isdigit():
        raise ValueError(f"Gradient base has to be a digit, got {base_str}.")

    base = int(base_str)
    if base < 16 or base > 231:
        raise ValueError("Gradient base must be between 16 and 232")

    while base > 52:
        base -= 36

    colors = []
    for i in range(6):
        colors.append(base + 36 * i)

    return _apply_colors(colors, item)
