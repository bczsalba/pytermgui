r"""
pytermgui.parser
----------------
author: bczsalba


This module provides a tokenizer for both ANSI and markup type strings,
and some higher level methods for converting between the two.

Major credit goes to https://github.com/willmcgugan/rich/blob/master/ansi.py,
the code here started out as a refactored version of his.


The tags available are:
    - /                                         (reset: 0)
    - bold                                      (1)
    - dim                                       (2)
    - italic                                    (3)
    - underline                                 (4)
    - blink                                     (5)
    - blink2                                    (6)
    - inverse                                   (7)
    - invisible                                 (8)
    - strikethrough                             (9)

    - removers of all of the above              ([ /{tag} ])

    - black                                     color code 0
    - red                                       color code 1
    - green                                     color code 2
    - yellow                                    color code 3
    - blue                                      color code 4
    - magenta                                   color code 5
    - cyan                                      color code 6
    - white                                     color code 7

    - 4-bit colors                              (0-16)
    - 8-bit colors                              (16-256)
    - 24-bit colors                             (RGB: [rrr;bbb;ggg], HEX: [#rr;bb;gg])
    - /fg                                       unset foreground color (go to default)
    - /bg                                       unset background color (go to default)

    - background versions of all of the above   ([ @{color} ])


Future:
    - !save                                     save current color attributes
    - !restore                                  restore saved color attributes


Notes on syntax:
    - Tags are escapable by putting a "\" before the opening square bracket, such as:
        "[bold italic] < these are parsed \[but this is not]"

    - The tokenizer only yields tokens if it is different from the previous one,
        so if your markup is `[bold bold bold]hello` it will only yield 1 bold token.

    - The tokenizer also implicitly adds a reset tag at the end of all strings it's given,
        if it doesn't already end in one.


Example syntax:
    >>> from pytermgui import ansi, markup

    >>> ansi = ansi(
    ... "[@141 60 bold italic] Hello "
    ... + "[/italic underline inverse] There! "
    ... )
    '\x1b[48;5;141m\x1b[38;5;60m\x1b[1m\x1b[3m Hello \x1b[23m\x1b[4m\x1b[7m There! \x1b[0m'

    >>> markup = markup(ansi)
    '[@141 60 bold italic]Hello[/italic underline inverse]There![/]''
"""

from __future__ import annotations

import re
from random import shuffle
from enum import Enum, auto as _auto
from dataclasses import dataclass
from typing import Optional, Iterator, Callable

from .exceptions import MarkupSyntaxError
from .ansi_interface import foreground, reset, bold


__all__ = [
    "define_tag",
    "define_macro",
    "escape_ansi",
    "tokenize_ansi",
    "tokenize_markup",
    "ansi",
    "markup",
    "prettify_markup",
    "optimize_ansi",
]

RE_ANSI = re.compile(r"(?:\x1b\[(.*?)m)|(?:\x1b\](.*?)\x1b\\)")
RE_TAGS = re.compile(r"""((\\*)\[([a-z0-9!#@\/].*?)\])""", re.VERBOSE)


def random_permutation(text: str) -> str:
    """Shuffle a string using random.shuffle on its list cast"""

    shuffled = list(text)
    shuffle(shuffled)

    return "".join(shuffled)


NAMES = [
    "/",
    "bold",
    "dim",
    "italic",
    "underline",
    "blink",
    "blink2",
    "inverse",
    "invisible",
    "strikethrough",
]

UNSET_MAP = {
    "/bold": "22",
    "/dim": "22",
    "/italic": "23",
    "/underline": "24",
    "/blink": "25",
    "/blink2": "26",
    "/inverse": "27",
    "/invisible": "28",
    "/strikethrough": "29",
    "/fg": "39",
    "/bg": "49",
}


MACRO_MAP = {
    "!upper": lambda item: item.upper(),
    "!lower": lambda item: item.lower(),
    "!title": lambda item: item.title(),
    "!capitalize": lambda item: item.capitalize(),
    "!random": random_permutation,
}

CUSTOM_MAP: dict[str, str] = {}
MacroCallable = Callable[[str], str]


def define_tag(name: str, value: str) -> None:
    """Define a custom markup tag to represent given value, supporting unsetters."""

    def strip_sequence(sequence: str) -> str:
        """Strip start & end chars of sequence to format it as a code"""

        sequence = sequence.lstrip("\x1b[")
        sequence = sequence.rstrip("m")

        return sequence

    if name.startswith("!"):
        raise ValueError('Only macro tags can always start with "!".')

    setter = ""
    unsetter = ""

    # Try to link to existing tag
    if value in CUSTOM_MAP:
        UNSET_MAP["/" + name] = value
        CUSTOM_MAP[name] = value
        return

    for token in tokenize_markup("[" + value + "]"):
        if token.plain is not None:
            continue

        setter += token.to_sequence()
        unsetter += Token(0, 0, code=token.get_unsetter()).to_sequence()

    UNSET_MAP["/" + name] = strip_sequence(unsetter)
    CUSTOM_MAP[name] = strip_sequence(setter)


def define_macro(name: str, value: MacroCallable) -> None:
    """Define custom markup macro"""

    if not name.startswith("!"):
        raise ValueError('Macro tags should always start with "!".')

    MACRO_MAP[name] = value


def escape_ansi(text: str) -> str:
    """Escape ANSI sequence"""

    return text.encode("unicode_escape").decode("utf-8")


def _handle_color(tag: str) -> Optional[tuple[str, bool]]:
    """Handle color fore/background, hex conversions"""

    # sort out non-colors
    if not all(char.isdigit() or char.lower() in "#;@abcdef" for char in tag):
        return None

    # convert into background color
    if tag.startswith("@"):
        pretext = "48;"
        tag = tag[1:]
    else:
        pretext = "38;"

    hexcolor = tag.startswith("#")

    # 8-bit (256) and 24-bit (RGB) colors use different id numbers
    color_pre = "5;" if tag.count(";") < 2 and not hexcolor else "2;"

    # hex colors are essentially RGB in a different format
    if hexcolor:
        try:
            tag = ";".join(str(val) for val in foreground.translate_hex(tag))
        except ValueError as error:
            raise SyntaxError(f'"{tag}" could not be converted to HEX.') from error

    return pretext + color_pre + tag, pretext == "48;"


def _handle_named_color(tag: str) -> Optional[tuple[str, int]]:
    """Check if name is in foreground.names and return its value if possible"""

    if not tag.lstrip("@") in foreground.names:
        return None

    if tag.startswith("@"):
        tag = tag[1:]
        background = "@"

    else:
        background = ""

    return _handle_color(background + str(foreground.names[tag]))


class TokenAttribute(Enum):
    """Special attribute for a Token"""

    CLEAR = _auto()
    COLOR = _auto()
    STYLE = _auto()
    MACRO = _auto()
    ESCAPED = _auto()
    BACKGROUND_COLOR = _auto()


@dataclass
class Token:
    """Result of ansi tokenized string."""

    start: int
    end: int
    plain: Optional[str] = None
    code: Optional[str] = None
    attribute: Optional[TokenAttribute] = None
    macro_value: Optional[MacroCallable] = None

    def to_name(self) -> str:
        """Convert token to named attribute for rich text"""

        if self.plain is not None:
            return self.plain

        # only one of [self.code, self.plain] can be None
        assert self.code is not None

        if self.code is not None and self.code.isdigit():
            if self.code in UNSET_MAP.values():
                for key, value in UNSET_MAP.items():
                    if value == self.code:
                        return key

            index = int(self.code)
            return NAMES[index]

        out = ""
        numbers = self.code.split(";")

        if numbers[0] == "48":
            out += "@"

        if len(numbers) < 3:
            raise SyntaxError(
                f'Invalid ANSI code "{escape_ansi(self.code)}" in token {self}.'
            )

        if not all(char.isdigit() for char in numbers):
            raise SyntaxError("Cannot convert non-digit to color.")

        simple = int(numbers[2])
        if len(numbers) == 3 and simple in foreground.names.values():
            for name, fore_value in foreground.names.items():
                if fore_value == simple:
                    return out + name

        out += ";".join(numbers[2:])

        return out

    def to_sequence(self) -> str:
        """Convert token to an ANSI sequence"""

        if self.code is None:
            # only one of [self.code, self.plain] can be None
            assert self.plain is not None
            return self.plain

        return "\x1b[" + self.code + "m"

    def get_unsetter(self) -> Optional[str]:
        """Get unset mapping for the current sequence"""

        if self.plain is not None:
            return None

        if self.attribute is TokenAttribute.CLEAR:
            return UNSET_MAP[self.to_name()]

        if self.attribute is TokenAttribute.COLOR:
            return UNSET_MAP["/fg"]

        if self.attribute is TokenAttribute.BACKGROUND_COLOR:
            return UNSET_MAP["/bg"]

        name = "/" + self.to_name()

        if not name in UNSET_MAP:
            raise KeyError(f"Could not find setter for token {self}.")

        return UNSET_MAP[name]

    def get_setter(self) -> Optional[str]:
        """Get set mapping for the current (unset) sequence"""

        if self.plain is not None or self.attribute is not TokenAttribute.CLEAR:
            return None

        if self.code == "0":
            return None

        name = self.to_name()
        if name in ["/fg", "/bg"]:
            return None

        name = name[1:]

        if not name in NAMES:
            raise ValueError(f"Could not find setter for token {self}.")

        return str(NAMES.index(name))


def tokenize_ansi(text: str) -> Iterator[Token]:
    """Tokenize text containing ANSI sequences
    Todo: add attributes to ansi tokens"""

    position = start = end = 0
    previous = None
    attribute: Optional[TokenAttribute]

    for match in RE_ANSI.finditer(text):
        start, end = match.span(0)
        sgr, _ = match.groups()

        # add plain text between last and current sequence
        if start > position:
            token = Token(start, end, plain=text[position:start])
            previous = token
            yield token

        if sgr.startswith("38;"):
            attribute = TokenAttribute.COLOR

        elif sgr.startswith("48;"):
            attribute = TokenAttribute.BACKGROUND_COLOR

        elif sgr == "0":
            attribute = TokenAttribute.CLEAR

        elif sgr.isnumeric() and int(sgr) in range(len(NAMES)):
            attribute = TokenAttribute.STYLE

        elif sgr in UNSET_MAP.values():
            attribute = TokenAttribute.CLEAR

        else:
            attribute = None

        token = Token(start, end, code=sgr, attribute=attribute)

        if previous is None or not previous.code == sgr:
            previous = token
            yield token

        position = end

    if position < len(text):
        yield Token(start, end, plain=text[position:])


def tokenize_markup(text: str, silence_exception: bool = False) -> Iterator[Token]:
    """Tokenize markup text"""

    position = 0
    start = end = 0

    for match in RE_TAGS.finditer(text):
        full, escapes, tag_text = match.groups()
        start, end = match.span()

        if start > position:
            yield Token(start, end, plain=text[position:start])

        if not escapes == "":
            yield Token(
                start, end, plain=full[len(escapes) :], attribute=TokenAttribute.ESCAPED
            )
            position = end

            continue

        for tag in tag_text.split():
            if tag in NAMES:
                yield Token(
                    start,
                    end,
                    code=str(NAMES.index(tag)),
                    attribute=(
                        TokenAttribute.CLEAR if tag == "/" else TokenAttribute.STYLE
                    ),
                )

            elif tag in UNSET_MAP:
                yield Token(
                    start,
                    end,
                    code=str(UNSET_MAP[tag]),
                    attribute=TokenAttribute.CLEAR,
                )

            elif tag in CUSTOM_MAP:
                yield Token(
                    start,
                    end,
                    code=CUSTOM_MAP[tag],
                    attribute=TokenAttribute.STYLE,  # maybe this could be a special CUSTOM tag
                )

            elif tag in MACRO_MAP:
                yield Token(
                    start,
                    end,
                    plain=tag,
                    code="",
                    macro_value=MACRO_MAP[tag],
                    attribute=TokenAttribute.MACRO,
                )

            else:
                named_color_info = _handle_named_color(tag)
                if named_color_info is not None:
                    code, background = named_color_info
                    yield Token(
                        start,
                        end,
                        code=code,
                        attribute=(
                            TokenAttribute.BACKGROUND_COLOR
                            if background
                            else TokenAttribute.COLOR
                        ),
                    )
                    continue

                color_info = _handle_color(tag)
                if color_info is not None:
                    color, background = color_info
                    yield Token(
                        start,
                        end,
                        code=color,
                        attribute=(
                            TokenAttribute.BACKGROUND_COLOR
                            if background
                            else TokenAttribute.COLOR
                        ),
                    )
                    continue

                elif not silence_exception:
                    raise MarkupSyntaxError(
                        tag=tag,
                        context=text,
                        cause="is not defined",
                    )

        position = end

    if position < len(text):
        yield Token(start, end, plain=text[position:])


def ansi(
    markup_text: str,
    ensure_reset: bool = True,
    ensure_optimized: bool = True,
    silence_exception: bool = False,
) -> str:
    """Turn markup text into ANSI str"""

    # TODO: Add support for unsetting macros

    def _apply_macros(text: str, macros: list[MacroCallable]) -> str:
        """Apply list of macros to string"""

        for macro in macros:
            text = macro(text)

        return text

    ansi_text = ""
    macro_callables: list[MacroCallable] = []

    for token in tokenize_markup(markup_text, silence_exception=silence_exception):
        if token.attribute is TokenAttribute.MACRO:
            assert token.macro_value is not None

            macro_callables.append(token.macro_value)
            continue

        if token.plain is not None:
            ansi_text += _apply_macros(token.plain, macro_callables)
        else:
            ansi_text += token.to_sequence()

    if ensure_reset and not ansi_text.endswith(reset()):
        ansi_text += reset()

    if ensure_optimized:
        return optimize_ansi(ansi_text, ensure_reset)

    return ansi_text


def markup(ansi_text: str, ensure_reset: bool = True) -> str:
    """Turn ansi text into markup"""

    markup_text = ""
    in_attr = False
    current_bracket: list[str] = []

    if ensure_reset and not ansi_text.endswith(reset()):
        ansi_text += reset()

    for token in tokenize_ansi(ansi_text):
        # start/add to attr bracket
        if token.code is not None:
            in_attr = True

            if token.code == "0":
                current_bracket = []
                if len(markup_text) > 0:
                    current_bracket.append("/")
                continue

            current_bracket.append(token.to_name())
            continue

        # close previous attr bracket
        if in_attr and len(current_bracket) > 0:
            markup_text += "[" + " ".join(current_bracket) + "]"
            current_bracket = []

        # add name with starting '[' escaped
        markup_text += token.to_name().replace("[", "\\[", 1)

    if len(current_bracket) > 0:
        markup_text += "[" + " ".join(current_bracket) + "]"

    return markup_text


def prettify_markup(markup_text: str) -> str:
    """Return syntax-highlighted markup"""

    def _style_attributes(attributes: list[Token]) -> str:
        """Style all attributes"""

        styled = bold("[")
        for i, item in enumerate(attributes):
            if i > 0:
                styled += " "

            if item.attribute is TokenAttribute.CLEAR:
                styled += foreground(item.to_name(), 210)
                continue

            if item.attribute is TokenAttribute.COLOR:
                styled += item.to_sequence() + item.to_name() + reset()
                continue

            if item.attribute is TokenAttribute.BACKGROUND_COLOR:
                numbers = item.to_sequence().split(";")
                numbers[0] = bold("", reset_style=False) + "\x1b[38"
                styled += ";".join(numbers) + item.to_name() + reset()
                continue

            if item.attribute is TokenAttribute.ESCAPED:
                chars = list(item.to_name())
                styled += foreground("\\" + chars[0], 210) + "".join(chars[1:])
                continue

            if item.attribute is TokenAttribute.MACRO:
                styled += bold(foreground(item.to_name(), 210))
                continue

            styled += item.to_sequence()

            styled += foreground(item.to_name(), 114)

        return styled + bold("]")

    visual_bracket: list[Token] = []
    applied_bracket: list[str] = []

    out = ""
    for token in tokenize_markup(markup_text):
        if token.code is not None:
            if token.attribute is TokenAttribute.CLEAR:
                name = token.to_name()
                if name == "/":
                    applied_bracket = []
                else:
                    offset = 21 if token.code == "22" else 20

                    sequence = "\x1b[" + str(int(token.code) - offset) + "m"
                    if sequence in applied_bracket:
                        applied_bracket.remove(sequence)

            applied_bracket.append(token.to_sequence())
            visual_bracket.append(token)
            continue

        if len(visual_bracket) > 0:
            out += _style_attributes(visual_bracket)
            visual_bracket = []

        name = token.to_name()
        if token.attribute is TokenAttribute.ESCAPED:
            name = "\\" + name

        out += "".join(applied_bracket) + name + reset()

    if len(visual_bracket) > 0:
        out += _style_attributes(visual_bracket)

    return out


def optimize_ansi(ansi_text: str, ensure_reset: bool = True) -> str:
    """Remove duplicate tokens & identical sequences"""

    out = ""
    sequence = ""
    previous = ""
    has_reset = False

    for token in tokenize_ansi(ansi_text):
        if token.code is not None:
            if token.code == "0":
                # only add reset code if there is a reason to
                if has_reset:
                    continue

                previous = sequence
                sequence = ""
                out += reset()

                has_reset = True
                continue

            sequence += token.to_sequence()
            has_reset = False
            continue

        # only add sequence if it doesn't match the previous one
        if not sequence == previous:
            out += sequence
            previous = sequence
            has_reset = False

        sequence = ""
        out += token.to_name()

    if ensure_reset and not out.endswith(reset()):
        out += reset()

    return out


if __name__ == "__main__":
    print(
        ansi(
            "[italic bold 141;35;60]hello there[/][141] alma[/] [18;218;168 underline]fa"
        )
    )
