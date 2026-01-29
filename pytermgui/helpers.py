"""Helper methods and functions for pytermgui."""

from __future__ import annotations

from typing import Iterator

from wcwidth import wrap as wcwidth_wrap

from .regex import real_length

__all__ = [
    "break_line",
]


def break_line(
    line: str, limit: int, non_first_limit: int | None = None, fill: str | None = None
) -> Iterator[str]:
    """Breaks a line into a `list[str]` with maximum `limit` length per line.

    Uses wcwidth.wrap() for proper word-boundary breaking, grapheme cluster
    handling, and wide character support. ANSI sequences are preserved and
    propagated across line breaks.

    Args:
        line: The line to split. May or may not contain ANSI sequences.
        limit: The maximum amount of characters allowed in each line, excluding
            non-printing sequences.
        non_first_limit: The limit after the first line. If not given, defaults
            to `limit`.
        fill: Optional character to pad lines to the limit width.
    """

    if line in ["", "\x1b[0m"]:
        yield ""
        return

    def _pad_line(text: str, width: int) -> str:
        if fill is None:
            return text

        count = width - real_length(text)
        if count > 0:
            return text + count * fill
        return text

    if non_first_limit is None:
        non_first_limit = limit

    for segment in line.split("\n"):
        if not segment:
            yield _pad_line("", limit)
            limit = non_first_limit
            continue

        wrapped = wcwidth_wrap(segment, limit)

        for wrapped_line in wrapped:
            yield _pad_line(wrapped_line, limit)
            limit = non_first_limit
