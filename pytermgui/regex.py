"""This modules contains all of the regex-related names and utilites."""

import re
from functools import lru_cache

RE_ANSI = re.compile(r"(?:\x1b\[(.*?)[mH])|(?:\x1b\](.*?)\x1b\\)|(?:\x1b_G(.*?)\x1b\\)")
RE_LINK = re.compile(r"(?:\x1b]8;;(.*?)\x1b\\(.*?)\x1b]8;;\x1b\\)")
RE_MACRO = re.compile(r"(![a-z0-9_]+)(?:\(([\w\/\.?\-=:]+)\))?")
RE_MARKUP = re.compile(r"((\\*)\[([^\[\]]+)\])")
RE_POSITION = re.compile(r"\x1b\[(\d+);(\d+)H")
RE_PIXEL_SIZE = re.compile(r"\x1b\[4;([\d]+);([\d]+)t")

RE_256 = re.compile(r"^([\d]{1,3})$")
RE_HEX = re.compile(r"(?:#)?([0-9a-fA-F]{6})")
RE_RGB = re.compile(r"(\d{1,3};\d{1,3};\d{1,3})")

__all__ = [
    "strip_ansi",
    "strip_markup",
    "real_length",
]


@lru_cache()
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


@lru_cache()
def strip_markup(text: str) -> str:
    """Removes markup tags from text.

    Args:
        text: A string or bytes object containing 0 or more markup tags.

    Returns:
        The text without any markup tags.
    """

    return RE_MARKUP.sub("", text)


@lru_cache(maxsize=1024)
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


@lru_cache(maxsize=1024)
def has_open_sequence(text: str) -> bool:
    """Figures out if the given text has any unclosed ANSI sequences.

    It supports standard SGR (`\\x1b[1mHello`), OSC (`\\x1b[30;2ST\\x1b\\\\`) and Kitty APC codes
    (`\x1b_Garguments;hex_data\\x1b\\\\`). It also recognizes incorrect syntax; it only considers
    a tag closed when it is using the right closing sequence, e.g. `m` or `H` for SGR, `\\x1b\\\\`
    for OSC and APC types.

    Args:
        text: The text to test.

    Returns:
        True if there is at least one tag that hasn't been closed, False otherwise.
    """

    is_osc = False
    is_sgr = False
    is_apc = False

    open_count = 0
    sequence = ""

    for char in text:
        if char == "\x1b":
            open_count += 1
            sequence += char
            continue

        if len(sequence) == 0:
            continue

        # Ignore OSC and APC closers as new openers
        if char == "\\" and sequence[-1] == "\x1b":
            open_count -= 1

        is_osc = is_osc or sequence[:2] == "\x1b]"
        is_sgr = is_sgr or sequence[:2] == "\x1b["
        is_apc = is_apc or sequence[:3] == "\x1b_G"

        sequence += char
        if (is_osc or is_apc) and sequence[-2:] == "\x1b\\":
            sequence = ""
            open_count -= 1

        elif is_sgr and char in {"m", "H"}:
            sequence = ""
            open_count -= 1

    return len(sequence) != 0 or open_count != 0
