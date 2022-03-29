"""This modules contains all of the regex-related names and utilites."""

import re

RE_ANSI = re.compile(r"(?:\x1b\[(.*?)[mH])|(?:\x1b\](.*?)\x1b\\)|(?:\x1b_G(.*?)\x1b\\)")
RE_LINK = re.compile(r"(?:\x1b]8;;(.*?)\x1b\\(.*?)\x1b]8;;\x1b\\)")
RE_MACRO = re.compile(r"(![a-z0-9_]+)(?:\(([\w\/\.?\-=:]+)\))?")
RE_MARKUP = re.compile(r"((\\*)\[([a-z0-9!#@_\/\(,\)].*?)\])")
RE_POSITION = re.compile(r"\x1b\[(\d+);(\d+)H")

RE_256 = re.compile(r"^([\d]{1,3})$")
RE_HEX = re.compile(r"(?:#)?([0-9a-fA-F]{6})")
RE_RGB = re.compile(r"(\d{1,3};\d{1,3};\d{1,3})")

__all__ = [
    "strip_ansi",
    "strip_markup",
    "real_length",
]


def strip_ansi(text: str) -> str:
    """Removes ANSI sequences from text.

    Args:
        text: A string or bytes object containing 0 or more ANSI sequences.

    Returns:
        The text without any ANSI sequences.
    """

    if hasattr(text, "plain"):
        return text.plain  # type: ignore

    return RE_ANSI.sub("", text)


def strip_markup(text: str) -> str:
    """Removes markup tags from text.

    Args:
        text: A string or bytes object containing 0 or more markup tags.

    Returns:
        The text without any markup tags.
    """

    return RE_MARKUP.sub("", text)


def real_length(text: str) -> int:
    """Gets the display-length of text.

    This length means no ANSI sequences are counted. This method is a convenience wrapper
    for `len(strip_ansi(text))`.

    Args:
        text: The text to calculate the length of.

    Returns:
        The display-length of text.
    """

    return len(strip_ansi(text))
