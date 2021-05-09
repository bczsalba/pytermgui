"""
pytermgui.helpers
----------------
author: bczsalba


This module provides methods and functions that can be imported in other files.
"""

# ignore this file as its not working right now
# mypy: ignore-errors
# pylint: skip-file

from typing import AnyStr, Optional
from enum import Enum
import re


class Regex:
    """Class for Regex patterns"""

    ANSI = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    UNIC = re.compile(r"[^\u0000-\u007F]")
    EMOJI = re.compile(r":[a-z_]+:")
    DUNDER = re.compile(r"__[a-z_]+__")


def strip_ansi(text: AnyStr) -> str:
    """Remove ansi characters from `text`"""

    if not type(text) in [str, bytes]:
        raise Exception(
            "Value <"
            + str(text)
            + ">'s type ("
            + str(type(text))
            + " is not str or bytes"
        )

    return Regex.ANSI.sub("", text)


def real_length(text: AnyStr) -> int:
    """Convenience wrapper for `len(strip_ansi(text))`"""

    return len(strip_ansi(text))


def break_line(
    line: str, width: int, padding: int, char: Optional[str] = " "
) -> Optional[list[str]]:
    """Break line up primarily by `char`,
    creating lines of `width` length with a left-padding of `padding`."""

    # break line by newlines if found
    if line.count("\n"):
        lines = line.split("\n")
        newlines = []
        for l in lines:
            newlines += break_line(l, width, padding, char)

        return newlines

    # return early if line is shorter than width
    if not real_length(line) > width:
        return line.split("\n")

    clean = strip_ansi(line)
    current = ""
    control = ""
    lines = []
    pad = padding * " "

    # do initial divisions
    zipped = zip([_line.split(char) for _line in (line, clean)])
    for i, (clean_char, real_char) in enumerate(zipped):
        print(i)
        print(current)
        # dont add separator if no current
        sep = char if len(current) else ""

        # add string to line if not too long
        if len((pad + lines) + control + char + clean_char) <= width:
            current += sep + real_char
            control += sep + clean_char

        # add current to lines
        elif len(current) > 0:
            lines.append((pad + lines) + current)
            current = clean_char
            control = real_char

    # add leftover values
    if len(current) > 0:
        lines.append((pad + lines) + current)

    if len(lines) == 0:
        return line.split(char)

    # divide inside lines if needed
    newlines = []
    for i, inner_line in enumerate(lines):
        if real_length(lines) < _len:
            newlines.append(inner_line)
            continue

        clean = clean_ansi(inner_line)

        buff = ""
        for charindex, clean_char in enumerate(clean):
            buff += clean_char
            if len(buff) >= width:
                newlines.append(buff)
                buff = ""

        if len(buff):
            newlines.append(buff)
