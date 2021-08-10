"""
pytermgui.helpers
----------------
author: bczsalba


This module provides methods and functions that can be imported in other files.
"""

from typing import Iterator
from .parser import tokenize_ansi, TokenAttribute, RE_ANSI, RE_TAGS
from .ansi_interface import reset

__all__ = [
    "strip_ansi",
    "strip_markup",
    "real_length",
    "get_sequences",
    "break_line",
]


def strip_ansi(text: str) -> str:
    """Remove ansi characters from `text`"""

    return RE_ANSI.sub("", text)


def strip_markup(text: str) -> str:
    """Remove markup characters from `text`"""

    return RE_TAGS.sub("", text)


def real_length(text: str) -> int:
    """Convenience wrapper for `len(strip_ansi(text))`"""

    return len(strip_ansi(text))


def get_sequences(text: str) -> str:
    """Get sequences from a string, optimized"""

    sequences = ""
    for token in tokenize_ansi(text):
        if token.code is not None:
            # remove sequence when its unsetter is encountered
            if token.attribute is TokenAttribute.CLEAR:
                setter_code = token.get_setter()

                # the token unsets a color, so we add
                # the unsetter sequence as-is
                if setter_code is None:
                    sequences += token.to_sequence()
                    continue

                setter = "\x1b[" + setter_code + "m"
                if setter in sequences:
                    sequences = sequences.replace(setter, "")

                continue

            sequences += token.to_sequence()

    return sequences


def break_line(  # pylint: disable=too-many-branches
    line: str, limit: int, char: str = " "
) -> Iterator[str]:
    """Break a line into a list[str] with maximum `limit` lengths"""

    # TODO: Refactor this method & handle newlines, avoid pylint disables.

    current = ""
    cur_len = 0
    chr_len = real_length(char)

    def _reset() -> None:
        """Add to lines and reset value"""

        nonlocal current, cur_len

        # get ansi tokens from old value
        new = get_sequences(current)

        current = new
        cur_len = real_length(new)

    def _should_yield() -> bool:
        """Decide if current is yieldable"""

        return real_length(current.rstrip()) > 0

    limit -= chr_len

    for word in line.split(char):
        new_len = real_length(word)

        # subdivide a word into right lengths
        if new_len > limit or "\n" in word:
            if _should_yield():
                yield current + reset()

            _reset()

            in_sequence = False
            sequence = ""
            end = len(word) - 1

            for i, character in enumerate(word):
                if character == "\x1b":
                    in_sequence = True
                    sequence = character
                    continue

                if character == "\n":
                    # TODO: Handle this case.
                    continue

                if in_sequence:
                    sequence += character

                    if not character == "m":
                        continue

                    in_sequence = False
                    character = sequence
                    sequence = ""

                current += character
                cur_len += real_length(character)

                if cur_len > limit:
                    # add splitting char if limit allows
                    if i == end and cur_len + chr_len <= limit:
                        current += char
                        cur_len += chr_len

                    if _should_yield():
                        yield current + reset()
                    _reset()

            continue

        # add current if we pass the limit
        if cur_len + new_len + chr_len > limit and _should_yield():
            yield current + reset()
            _reset()

        current += word + char
        cur_len += new_len + chr_len

    current = current.rstrip()
    if _should_yield():
        yield current + reset()
