"""
Helper methods and functions for pytermgui.
"""

from typing import Iterator
from .parser import markup, TokenType, RE_ANSI, RE_MARKUP, StyledText
from .ansi_interface import reset

__all__ = ["strip_ansi", "strip_markup", "real_length", "get_sequences", "break_line"]


def strip_ansi(text: str) -> str:
    """Removes ANSI sequences from text.

    Args:
        text: A string or bytes object containing 0 or more ANSI sequences.

    Returns:
        The text without any ANSI sequences.
    """

    if isinstance(text, StyledText):
        return text.plain

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


def get_sequences(text: str) -> str:
    """Extracts ANSI sequences from text.

    Args:
        text: The text to operate on.

    Returns:
        All sequences found.
    """

    sequences = ""
    for token in markup.tokenize_ansi(text):
        if token.sequence is not None:
            # remove sequence when its unsetter is encountered
            if token.ttype is TokenType.UNSETTER:
                setter_code = token.sequence

                # the token unsets a color, so we add
                # the unsetter sequence as-is
                if setter_code is None:
                    sequences += setter_code
                    continue

                setter = "\x1b[" + setter_code + "m"
                if setter in sequences:
                    sequences = sequences.replace(setter, "")

                continue

            sequences += token.sequence

    return sequences


def break_line(  # pylint: disable=too-many-branches
    line: str, limit: int, char: str = " "
) -> Iterator[str]:
    """Breaks a line into a `list[str]` with maximum `limit` length per line.

    ANSI sequences are not counted into the length, and styling stays consistent
    even between lines.

    Args:
        line: The line to break up.
        limit: The maximum width of a line, counting with `real_length`.
        char: The character that separates words. Defaults to a space.

    Note:
        This function currently does NOT handle literal newlines ("\\n"), instead
        chosing to throw them away. You can get around this by splitting your text
        by newlines prior to handing it to `break_line`.

    Yields:
        Lines of maximum limit real_length.
    """

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
                    # TODO: Handle newlines
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
                        yield current.rstrip() + reset()
                    _reset()

            continue

        # add current if we pass the limit
        if cur_len + new_len + chr_len > limit and _should_yield():
            yield current.rstrip() + reset()
            _reset()

        current += word + char
        cur_len += new_len + chr_len

    current = current.rstrip()
    if _should_yield():
        yield current.rstrip() + reset()
