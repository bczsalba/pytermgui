"""Helper methods and functions for pytermgui."""

from __future__ import annotations

from typing import Iterator

from .colors import Color
from .ansi_interface import reset
from .parser import markup, TokenType, Token

__all__ = [
    "get_applied_sequences",
    "break_line",
]


def get_applied_sequences(text: str) -> str:
    """Extracts ANSI sequences from text.

    Args:
        text: The text to operate on.

    Returns:
        All sequences found.
    """

    tokens: list[Token] = []
    reset_char = reset()
    for token in markup.tokenize_ansi(text):
        if not token.ttype is TokenType.UNSETTER:
            tokens.append(token)
            continue

        assert token.sequence is not None
        if token.sequence == reset_char:
            tokens = []
            continue

        name = token.name.lstrip("/")
        for style in tokens.copy():
            if name in ["fg", "bg"] and style.ttype is TokenType.COLOR:
                color = style.data
                assert isinstance(color, Color)

                if name == "fg" and not color.background:
                    tokens.remove(style)
                elif name == "bg" and color.background:
                    tokens.remove(style)

            elif style.name == name:
                tokens.remove(style)

        continue

    return "".join(token.sequence or "" for token in tokens)


def break_line(
    line: str, limit: int, non_first_limit: int | None = None
) -> Iterator[str]:
    """Breaks a line into a `list[str]` with maximum `limit` length per line.

    It keeps ongoing ANSI sequences between lines, and inserts a reset sequence
    at the end of each style-containing line.

    At the moment it splits strings exactly on the limit, and not on word
    boundaries. That functionality would be preferred, so it will end up being
    implemented at some point.

    Args:
        line: The line to split. May or may not contain ANSI sequences.
        limit: The maximum amount of characters allowed in each line, excluding
            non-printing sequences.
        non_first_limit: The limit after the first line. If not given, defaults
            to `limit`.
    """

    used = 0
    current = ""
    sequences = ""

    if non_first_limit is None:
        non_first_limit = limit

    for token in markup.tokenize_ansi(line):
        if token.sequence is None:
            assert isinstance(token.data, str)
            for char in token.data:
                if char == "\n" or used >= limit:
                    if sequences != "":
                        current += "\x1b[0m"

                    yield current

                    current = sequences
                    used = 0

                    limit = non_first_limit

                if char != "\n":
                    current += char
                    used += 1

            continue

        if token.sequence == "\x1b[0m":
            sequences = "\x1b[0m"

            if len(current) > 0:
                current += sequences

            continue

        sequences += token.sequence
        current += token.sequence

    if current == "":
        return

    if sequences != "" and not current.endswith("\x1b[0m"):
        current += "\x1b[0m"

    yield current
