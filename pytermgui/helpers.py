"""Helper methods and functions for pytermgui."""

from __future__ import annotations

from typing import Iterator

from .markup import tokenize_ansi
from .markup.parsing import LINK_TEMPLATE, PARSERS
from .regex import real_length

__all__ = [
    "break_line",
]


def break_line(  # pylint: disable=too-many-branches
    line: str, limit: int, non_first_limit: int | None = None, fill: str | None = None
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

    if line in ["", "\x1b[0m"]:
        yield ""
        return

    def _pad_and_link(line: str, link: str | None) -> str:
        count = limit - real_length(line)

        if link is not None:
            line = LINK_TEMPLATE.format(uri=link, label=line)

        if fill is None:
            return line

        line += count * fill

        return line

    used = 0
    current = ""
    sequences = ""

    if non_first_limit is None:
        non_first_limit = limit

    parsers = PARSERS
    link = None

    for token in tokenize_ansi(line):
        if token.is_plain():
            for char in token.value:
                if char == "\n" or used >= limit:
                    if sequences != "":
                        current += "\x1b[0m"

                    yield _pad_and_link(current, link)
                    link = None

                    current = sequences
                    used = 0

                    limit = non_first_limit

                if char != "\n":
                    current += char
                    used += 1

            # If the link wasn't yielded along with its token, remove and add it
            # to current manually.
            if link is not None:
                current = current[: -len(token.value)]
                current += LINK_TEMPLATE.format(uri=link, label=token.value)
                link = None

            continue

        if token.value == "/":
            sequences = "\x1b[0m"

            if len(current) > 0:
                current += sequences

            continue

        if token.is_hyperlink():
            link = token.value
            continue

        sequence = parsers[type(token)](token, {}, lambda: line)  # type: ignore
        sequences += sequence
        current += sequence

    if current == "":
        return

    if sequences != "" and not current.endswith("\x1b[0m"):
        current += "\x1b[0m"

    yield _pad_and_link(current, link)
