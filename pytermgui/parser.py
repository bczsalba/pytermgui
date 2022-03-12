"""
This module provides `TIM`, PyTermGUI's Terminal Inline Markup language. It is a simple,
performant and easy to read way to style, colorize & modify text.

Basic rundown
-------------

TIM is included with the purpose of making styling easier to read and manage.

Its syntax is based on square brackets, within which tags are strictly separated by one
space character. Tags can stand for colors (xterm-256, RGB or HEX, both background &
foreground), styles, unsetters and macros.

The 16 simple colors of the terminal exist as named tags that refer to their numerical
value.

Here is a simple example of the syntax, using the `pytermgui.pretty` submodule to
syntax-highlight it inside the REPL:

```python3
>>> from pytermgui import pretty
>>> '[141 @61 bold] Hello [!upper inverse] There '
```

<p align=center>
<img src="https://github.com/bczsalba/pytermgui/blob/master/assets/docs/parser/\
simple_example.png?raw=true" width=70%>
</p>


General syntax
--------------

Background colors are always denoted by a leading `@` character in front of the color
tag. Styles are just the name of the style and macros have an exclamation mark in front
of them. Additionally, unsetters use a leading slash (`/`) for their syntax. Color
tokens have special unsetters: they use `/fg` to cancel foreground colors, and `/bg` to
do so with backgrounds.

### Macros:

Macros are any type of callable that take at least *args; this is the value of the plain
text enclosed by the tag group within which the given macro resides. Additionally,
macros can be given any number of positional arguments from within markup, using the
syntax:

```
[!macro(arg1:arg2:arg3)]Text that the macro applies to.[/!macro]plain text, no macro
```

This syntax gets parsed as follows:

```python3
macro("Text that the macro applies to.", "arg1", "arg2", "arg3")
```

`macro` here is whatever the name `macro` was defined as prior.

### Colors:

Colors can be of three general types: xterm-256, RGB and HEX.

`xterm-256` stands for one of the 256 xterm colors. You can use `ptg -c` to see the all
of the available colors. Its syntax is just the 0-base index of the color, like `[141]`

`RGB` colors are pretty self explanatory. Their syntax is follows the format
`RED;GREEN;BLUE`, such as `[111;222;333]`.

`HEX` colors are basically just RGB with extra steps. Their syntax is `#RRGGBB`, such as
`[#FA72BF]`. This code then gets converted to a tuple of RGB colors under the hood, so
from then on RGB and HEX colors are treated the same, and emit the same tokens.

As mentioned above, all colors can be made to act on the background instead by
prepending the color tag with `@`, such as `@141`, `@111;222;333` or `@#FA72BF`. To
clear these effects, use `/fg` for foreground and `/bg` for background colors.

`MarkupLanguage` and instancing
-------------------------------

All markup behaviour is done by an instance of the `MarkupLanguage` class. This is done
partially for organization reasons, but also to allow a sort of sandboxing of custom
definitions and settings.

PyTermGUI provides the `tim` name as the global markup language instance. For historical
reasons, the same instance is available as `markup`. This should be used pretty much all
of the time, and custom instances should only ever come about when some
security-sensitive macro definitions are needed, as `markup` is used by every widget,
including user-input ones such as `InputField`.

For the rest of this page, `MarkupLanguage` will refer to whichever instance you are
using.

TL;DR : Use `tim` always, unless a security concern blocks you from doing so.

Caching
-------

By default, all markup parse results are cached and returned when the same input is
given. To disable this behaviour, set your markup instance (usually `markup`)'s
`should_cache` field to False.

Customization
-------------

There are a couple of ways to customize how markup is parsed. Custom tags can be created
by calling `MarkupLanguage.alias`. For defining custom macros, you can use
`MarkupLanguage.define`. For more information, see each method's documentation.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

import re
from random import shuffle
from dataclasses import dataclass
from argparse import ArgumentParser
from enum import Enum, auto as _auto
from typing import Iterator, Callable, Tuple, List

from .ansi_interface import foreground
from .exceptions import MarkupSyntaxError, AnsiSyntaxError


__all__ = [
    "MacroCallable",
    "MacroCall",
    "MarkupLanguage",
    "StyledText",
    "markup",
    "tim",
]

MacroCallable = Callable[..., str]
MacroCall = Tuple[MacroCallable, List[str]]

RE_ANSI = re.compile(r"(?:\x1b\[(.*?)m)|(?:\x1b\](.*?)\x1b\\)|(?:\x1b_G(.*?)\x1b\\)")
RE_MACRO = re.compile(r"(![a-z0-9_]+)(?:\(([\w\/\.?\-=:]+)\))?")
RE_MARKUP = re.compile(r"((\\*)\[([a-z0-9!#@_\/\(,\)].*?)\])")

RE_256 = re.compile(r"^([\d]{1,3})$")
RE_HEX = re.compile(r"#([0-9a-fA-F]{6})")
RE_RGB = re.compile(r"(\d{1,3};\d{1,3};\d{1,3})")

STYLE_MAP = {
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
    "blink": "5",
    "blink2": "6",
    "inverse": "7",
    "invisible": "8",
    "strikethrough": "9",
    "overline": "53",
}

UNSETTER_MAP: dict[str, str | None] = {
    "/": "0",
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
    "/overline": "54",
}


def macro_align(width: str, alignment: str, content: str) -> str:
    """Aligns given text using fstrings.

    Args:
        width: The width to align to.
        alignment: One of "left", "center", "right".
        content: The content to align; implicit argument.
    """

    aligner = "<" if alignment == "left" else (">" if alignment == "right" else "^")
    return f"{content:{aligner}{width}}"


def macro_expand(lang: MarkupLanguage, tag: str) -> str:
    """Expands a tag alias."""

    if not tag in lang.user_tags:
        return tag

    return lang.get_markup("\x1b[" + lang.user_tags[tag] + "m ")[:-1]


def macro_strip_fg(item: str) -> str:
    """Strips foreground color from item"""

    return markup.parse("[/fg]" + item)


def macro_strip_bg(item: str) -> str:
    """Strips foreground color from item"""

    return markup.parse("[/bg]" + item)


def macro_shuffle(item: str) -> str:
    """Shuffles a string using shuffle.shuffle on its list cast."""

    shuffled = list(item)
    shuffle(shuffled)

    return "".join(shuffled)


def macro_link(*args) -> str:
    """Creates a clickable hyperlink.

    Note:
        Since this is a pretty new feature for terminals, its support is limited.
    """

    *uri_parts, label = args
    uri = ":".join(uri_parts)

    return f"\x1b]8;;{uri}\x1b\\{label}\x1b]8;;\x1b\\"


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

    return markup.parse(out)


def macro_rainbow(item: str) -> str:
    """Creates rainbow-colored text."""

    colors = ["red", "208", "yellow", "green", "brightblue", "blue", "93"]

    return _apply_colors(colors, item)


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


class TokenType(Enum):
    """An Enum to store various token types."""

    PLAIN = _auto()
    """Plain text, nothing interesting."""

    STYLE = _auto()
    """A builtin terminal style, such as `bold` or `italic`."""

    MACRO = _auto()
    """A PTG markup macro. The macro itself is stored inside `self.data`."""

    ESCAPED = _auto()
    """An escaped token."""

    FG_8BIT = _auto()
    """8 bit (xterm-255) foreground color."""

    BG_8BIT = _auto()
    """8 bit (xterm-255) background color."""

    FG_24BIT = _auto()
    """24 bit (RGB) foreground color."""

    BG_24BIT = _auto()
    """24 bit (RGB) background color."""

    UNSETTER = _auto()
    """A token that unsets some other attribute."""


@dataclass
class Token:
    """A class holding information on a singular markup or ANSI style unit.

    Attributes:
    """

    ttype: TokenType
    """The type of this token."""

    data: str | MacroCall | None
    """The data contained within this token. This changes based on the `ttype` attr."""

    name: str = "<unnamed-token>"
    """An optional display name of the token. Defaults to `data` when not given."""

    def __post_init__(self) -> None:
        """Sets `name` to `data` if not provided."""

        if self.name == "<unnamed-token>":
            assert isinstance(self.data, str)
            self.name = self.data

    def __eq__(self, other: object) -> bool:
        """Checks equality with `other`."""

        if other is None:
            return False

        if not isinstance(other, Token):
            raise NotImplementedError(
                "Cannot check for equality between Token and non-Token of type"
                + f" {type(other)}."
            )

        return other.data == self.data and other.ttype is self.ttype

    @property
    def sequence(self) -> str | None:
        """Returns the ANSI sequence this token represents."""

        if self.data is None:
            return None

        if self.ttype in [TokenType.PLAIN, TokenType.MACRO, TokenType.ESCAPED]:
            return None

        assert isinstance(self.data, str)
        data = self.data.lstrip("@")

        if self.ttype in [TokenType.STYLE, TokenType.UNSETTER]:
            return "\033[" + data + "m"

        # Handle colors
        if self.ttype.name.startswith("BG"):
            template = "\x1b[48;{c_id};" + data + "m"
        else:
            template = "\x1b[38;{c_id};" + data + "m"

        if self.ttype in [TokenType.FG_8BIT, TokenType.BG_8BIT]:
            return template.format(c_id="5")

        return template.format(c_id="2")


class StyledText(str):
    """A styled text object.

    The purpose of this class is to implement some things regular `str`
    breaks at when encountering ANSI sequences.

    Instances of this class are usually spat out by `MarkupLanguage.parse`,
    but may be manually constructed if the need arises. Everything works even
    if there is no ANSI tomfoolery going on.
    """

    value: str
    """The underlying, ANSI-inclusive string value."""

    plain: str
    """The string value with no ANSI sequences."""

    tokens: list[Token]
    """The list of tokens that make up this string."""

    def __new__(cls, value: str = ""):
        """Creates a StyledText, gets markup tags.

        Args:
            markup_language: The markup language instance this object uses.
        """

        obj = super().__new__(cls, value)
        obj.value = value
        obj.tokens = list(markup.tokenize_ansi(value))

        obj.plain = ""
        for token in obj.tokens:
            if token.ttype is not TokenType.PLAIN:
                continue

            assert isinstance(token.data, str)
            obj.plain += token.data

        return obj

    def plain_index(self, index: int | None) -> int | None:
        """Finds given index inside plain text."""

        if index is None:
            return None

        styled_chars = 0
        plain_chars = 0
        negative_index = False

        tokens = self.tokens.copy()
        if index < 0:
            tokens.reverse()
            index = abs(index)
            negative_index = True

        for token in tokens:
            if token.data is None:
                continue

            if token.ttype is not TokenType.PLAIN:
                assert token.sequence is not None
                styled_chars += len(token.sequence)
                continue

            for _ in range(len(token.data)):
                if plain_chars == index:
                    if negative_index:
                        return -1 * (plain_chars + styled_chars)

                    return styled_chars + plain_chars

                plain_chars += 1

        return None

    def __len__(self) -> int:
        """Gets "real" length of object."""

        return len(self.plain)

    def __getitem__(self, subscript: int | slice) -> str:
        """Gets an item, adjusted for non-plain text.

        Args:
            subscript: The integer or slice to find.

        Returns:
            The elements described by the subscript.

        Raises:
            IndexError: The given index is out of range.
        """

        if isinstance(subscript, int):
            plain_index = self.plain_index(subscript)
            if plain_index is None:
                raise IndexError("StyledText index out of range")

            return self.value[plain_index]

        return self.value[
            slice(
                self.plain_index(subscript.start),
                self.plain_index(subscript.stop),
                subscript.step,
            )
        ]


class MarkupLanguage:
    """A class representing an instance of a Markup Language.

    This class is used for all markup/ANSI parsing, tokenizing and usage.

    ```python3
    from pytermgui import tim

    tim.alias("my-tag", "@152 72 bold")
    tim.print("This is [my-tag]my-tag[/]!")
    ```

    <p style="text-align: center">
        <img src="https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/\
docs/parser/markup_language.png"
        style="width: 80%">
    </p>
    """

    raise_unknown_markup: bool = False
    """Raise `pytermgui.exceptions.MarkupSyntaxError` when encountering unknown markup tags."""

    def __init__(self, default_macros: bool = True) -> None:
        """Initializes a MarkupLanguage.

        Args:
            default_macros: If not set, the builtin macros are not defined.
        """

        self.tags: dict[str, str] = STYLE_MAP.copy()
        self._cache: dict[str, StyledText] = {}
        self.macros: dict[str, MacroCallable] = {}
        self.user_tags: dict[str, str] = {}
        self.unsetters: dict[str, str | None] = UNSETTER_MAP.copy()

        self.should_cache: bool = True

        if default_macros:
            self.define("!link", macro_link)
            self.define("!align", macro_align)
            self.define("!markup", self.get_markup)
            self.define("!shuffle", macro_shuffle)
            self.define("!strip_bg", macro_strip_bg)
            self.define("!strip_fg", macro_strip_fg)
            self.define("!rainbow", macro_rainbow)
            self.define("!gradient", macro_gradient)
            self.define("!upper", lambda item: str(item.upper()))
            self.define("!lower", lambda item: str(item.lower()))
            self.define("!title", lambda item: str(item.title()))
            self.define("!capitalize", lambda item: str(item.capitalize()))
            self.define("!expand", lambda tag: macro_expand(self, tag))
            self.define("!debug", lambda *args: ",".join(ascii(arg) for arg in args))

        self.alias("pprint-int", "175")
        self.alias("pprint-str", "142")
        self.alias("pprint-type", "214")
        self.alias("pprint-none", "167")

        self.alias("inspector-name", "pprint-type")
        self.alias("inspector-file", "109")
        self.alias("inspector-keyword", "203")

    @staticmethod
    def _get_color_token(tag: str) -> Token | None:
        """Tries to get a color token from the given tag.

        Args:
            tag: The tag to parse.

        Returns:
            A color token if the given tag could be parsed into one, else None.
        """

        def _hex_to_rgb(color: str) -> str:
            """Get rgb color from hex"""

            return ";".join(str(int(color[i : i + 2], 16)) for i in (0, 2, 4))

        background = tag.startswith("@")
        lookup_tag = tag
        if background:
            lookup_tag = tag[1:]

        if lookup_tag in foreground.names:
            return Token(
                name=tag,
                ttype=(TokenType.BG_8BIT if background else TokenType.FG_8BIT),
                data=str(foreground.names[lookup_tag]),
            )

        data_256 = RE_256.match(lookup_tag)
        if data_256 is not None:
            return Token(
                name=tag,
                ttype=(TokenType.BG_8BIT if background else TokenType.FG_8BIT),
                data=lookup_tag,
            )

        data_hex = RE_HEX.match(lookup_tag)
        if data_hex is not None:
            return Token(
                name=tag,
                ttype=(TokenType.BG_24BIT if background else TokenType.FG_24BIT),
                data=_hex_to_rgb(lookup_tag[1:]),
            )

        data_rgb = RE_RGB.match(lookup_tag)
        if data_rgb is not None:
            return Token(
                name=tag,
                ttype=(TokenType.BG_24BIT if background else TokenType.FG_24BIT),
                data=lookup_tag,
            )

        return None

    def _get_style_token(self, tag: str) -> Token | None:
        """Tries to get a style (including unsetter) token from tags, user tags and unsetters.

        Args:
            tag: The tag to parse.

        Returns:
            A `Token` if one could be created, None otherwise.
        """

        if tag in self.unsetters:
            return Token(name=tag, ttype=TokenType.UNSETTER, data=self.unsetters[tag])

        if tag in self.user_tags:
            return Token(name=tag, ttype=TokenType.STYLE, data=self.user_tags[tag])

        if tag in self.tags:
            return Token(name=tag, ttype=TokenType.STYLE, data=self.tags[tag])

        return None

    def print(self, *args, **kwargs) -> None:
        """Parse all arguments and pass them through to print, along with kwargs."""

        parsed = []
        for arg in args:
            parsed.append(self.parse(str(arg)))

        print(*parsed, **kwargs)

    def tokenize_markup(self, markup_text: str) -> Iterator[Token]:
        """Converts the given markup string into an iterator of `Token`.

        Args:
            markup_text: The text to look at.

        Returns:
            An iterator of tokens. The reason this is an iterator is to possibly save
            on memory.
        """

        end = 0
        start = 0
        cursor = 0
        for match in RE_MARKUP.finditer(markup_text):
            full, escapes, tag_text = match.groups()
            start, end = match.span()

            # Add plain text between last and current match
            if start > cursor:
                yield Token(ttype=TokenType.PLAIN, data=markup_text[cursor:start])

            if not escapes == "" and len(escapes) % 2 == 1:
                cursor = end
                yield Token(ttype=TokenType.ESCAPED, data=full[len(escapes) :])
                continue

            for tag in tag_text.split():
                token = self._get_style_token(tag)
                if token is not None:
                    yield token
                    continue

                # Try to find a color token
                token = self._get_color_token(tag)
                if token is not None:
                    yield token
                    continue

                macro_match = RE_MACRO.match(tag)
                if macro_match is not None:
                    name, args = macro_match.groups()
                    macro_args = () if args is None else args.split(":")

                    if not name in self.macros:
                        raise MarkupSyntaxError(
                            tag=tag,
                            cause="is not a defined macro",
                            context=markup_text,
                        )

                    yield Token(
                        name=tag,
                        ttype=TokenType.MACRO,
                        data=(self.macros[name], macro_args),
                    )
                    continue

                if self.raise_unknown_markup:
                    raise MarkupSyntaxError(
                        tag=tag, cause="not defined", context=markup_text
                    )

            cursor = end

        # Add remaining text as plain
        if len(markup_text) > cursor:
            yield Token(ttype=TokenType.PLAIN, data=markup_text[cursor:])

    def tokenize_ansi(  # pylint: disable=too-many-branches
        self, ansi: str
    ) -> Iterator[Token]:
        """Converts the given ANSI string into an iterator of `Token`.

        Args:
            ansi: The text to look at.

        Returns:
            An iterator of tokens. The reason this is an iterator is to possibly save
            on memory.
        """

        end = 0
        start = 0
        cursor = 0

        # StyledText messes with indexing, so we need to cast it
        # back to str.
        if isinstance(ansi, StyledText):
            ansi = str(ansi)

        for match in RE_ANSI.finditer(ansi):
            code = match.groups()[0]
            start, end = match.span()
            if code is None:
                continue

            parts = code.split(";")

            if start > cursor:
                plain = ansi[cursor:start]

                yield Token(name=plain, ttype=TokenType.PLAIN, data=plain)

            # Styles & unsetters
            if len(parts) == 1:
                token_code: str | None = ""
                for name, token_code in self.unsetters.items():
                    if token_code == parts[0]:
                        ttype = TokenType.UNSETTER
                        break
                else:
                    for name, token_code in self.tags.items():
                        if token_code == parts[0]:
                            ttype = TokenType.STYLE
                            break
                    else:

                        raise AnsiSyntaxError(
                            tag=parts[0], cause="not recognized", context=ansi
                        )

                yield Token(name=name, ttype=ttype, data=token_code)

            # Colors
            elif len(parts) >= 3:
                name = ";".join(parts[2:])

                types = [TokenType.FG_8BIT, TokenType.FG_24BIT]

                if parts[0] == "48":
                    name = "@" + name
                    types = [TokenType.BG_8BIT, TokenType.BG_24BIT]

                ttype = types[0] if parts[1] == "5" else types[1]

                yield Token(ttype=ttype, data=name)

            cursor = end

        if cursor < len(ansi):
            plain = ansi[cursor:]

            yield Token(ttype=TokenType.PLAIN, data=plain)

    def define(self, name: str, method: MacroCallable) -> None:
        """Defines a Macro tag that executes the given method.

        Args:
            name: The name the given method will be reachable by within markup.
                The given value gets "!" prepended if it isn't present already.
            method: The method this macro will execute.
        """

        if not name.startswith("!"):
            name = "!" + name

        self.macros[name] = method
        self.unsetters["/" + name] = None

    def alias(self, name: str, value: str) -> None:
        """Aliases the given name to a value, and generates an unsetter for it.

        Note that it is not possible to alias macros.

        Args:
            name: The name of the new tag.
            value: The value the new tag will stand for.
        """

        def _get_unsetter(token: Token) -> str | None:
            """Get unsetter for a token"""

            if token.ttype is TokenType.PLAIN:
                return None

            if token.ttype is TokenType.UNSETTER:
                return self.unsetters[token.name]

            if token.ttype.name.startswith("FG"):
                return self.unsetters["/fg"]

            if token.ttype.name.startswith("BG"):
                return self.unsetters["/bg"]

            name = "/" + token.name
            if not name in self.unsetters:
                raise KeyError(f"Could not find unsetter for token {token}.")

            return self.unsetters[name]

        if name.startswith("!"):
            raise ValueError('Only macro tags can always start with "!".')

        setter = ""
        unsetter = ""

        # Try to link to existing tag
        if value in self.user_tags:
            self.unsetters["/" + name] = self.unsetters["/" + value]
            self.user_tags[name] = self.user_tags[value]
            return

        for token in self.tokenize_markup("[" + value + "]"):
            if token.ttype is TokenType.PLAIN:
                continue

            assert token.sequence is not None
            setter += token.sequence

            t_unsetter = _get_unsetter(token)
            assert t_unsetter is not None
            unsetter += "\x1b[" + t_unsetter + "m"

        self.unsetters["/" + name] = unsetter.lstrip("\x1b[").rstrip("m")
        self.user_tags[name] = setter.lstrip("\x1b[").rstrip("m")

        marked: list[str] = []
        for item in self._cache:
            if name in item:
                marked.append(item)

        for item in marked:
            del self._cache[item]

    # TODO: I cannot cut down the one-too-many branch that this has at the moment.
    #       We could look into it in the future, however.
    def parse(  # pylint: disable=too-many-branches
        self, markup_text: str
    ) -> StyledText:
        """Parses the given markup.

        Args:
            markup_text: The markup to parse.

        Returns:
            A `StyledText` instance of the result of parsing the input. This
            custom `str` class is used to allow accessing the plain value of
            the output, as well as to cleanly index within it. It is analogous
            to builtin `str`, only adds extra things on top.
        """

        applied_macros: list[tuple[str, MacroCall]] = []
        previous_token: Token | None = None
        previous_sequence = ""
        sequence = ""
        out = ""

        def _apply_macros(text: str) -> str:
            """Apply current macros to text"""

            for _, (method, args) in applied_macros:
                text = method(*args, text)

            return text

        def _is_same_colorgroup(previous: Token, new: Token) -> bool:
            color_types = [
                TokenType.FG_8BIT,
                TokenType.BG_8BIT,
                TokenType.FG_24BIT,
                TokenType.BG_24BIT,
            ]

            if not (previous.ttype in color_types and token.ttype in color_types):
                return False

            prev_prefix = previous.ttype.name.split("_")[0]
            prefix = new.ttype.name.split("_")[0]
            return prev_prefix == prefix

        if (
            RE_MACRO.match(markup_text) is not None
            and self.should_cache
            and markup_text in self._cache
        ):
            return self._cache[markup_text]

        token: Token
        for token in self.tokenize_markup(markup_text):
            if sequence != "" and previous_token == token:
                continue

            # Optimize out previously added color tokens, as only the most
            # recent would be visible anyways.
            if (
                token.sequence is not None
                and previous_token is not None
                and _is_same_colorgroup(previous_token, token)
            ):
                sequence = token.sequence
                continue

            if token.ttype == TokenType.UNSETTER and token.data == "0":
                out += "\033[0m"
                sequence = ""
                continue

            previous_token = token

            # Macro unsetters are stored with None as their data
            if token.data is None and token.ttype is TokenType.UNSETTER:
                for item, data in applied_macros:
                    macro_match = RE_MACRO.match(item)
                    assert macro_match is not None

                    macro_name = macro_match.groups()[0]

                    if "/" + macro_name == token.name:
                        applied_macros.remove((item, data))

                continue

            if token.ttype is TokenType.MACRO:
                assert isinstance(token.data, tuple)

                applied_macros.append((token.name, token.data))
                continue

            if token.sequence is None:
                applied = sequence
                for item in previous_sequence.split("\x1b"):
                    if item == "":
                        continue

                    item = "\x1b" + item
                    applied = applied.replace(item, "")

                out += applied + _apply_macros(token.name)
                previous_sequence = sequence
                sequence = ""
                continue

            sequence += token.sequence

        if sequence + previous_sequence != "":
            out += "\x1b[0m"

        out = StyledText(out)
        self._cache[markup_text] = out
        return out

    def get_markup(self, ansi: str) -> str:
        """Generates markup from ANSI text.

        Args:
            ansi: The text to get markup from.

        Returns:
            A markup string that can be parsed to get (visually) the same
            result. Note that this conversion is lossy in a way: there are some
            details (like macros) that cannot be preserved in an ANSI->Markup->ANSI
            conversion.
        """

        current_tags: list[str] = []
        out = ""
        for token in self.tokenize_ansi(ansi):
            if token.ttype is TokenType.PLAIN:
                if len(current_tags) != 0:
                    out += "[" + " ".join(current_tags) + "]"

                assert isinstance(token.data, str)
                out += token.data
                current_tags = []
                continue

            current_tags.append(token.name)

        return out

    def prettify_ansi(self, text: str) -> str:
        """Returns a prettified (syntax-highlighted) ANSI str.

        This is useful to quickly "inspect" a given ANSI string. However,
        for most real uses `MarkupLanguage.prettify_markup` would be
        preferable, given an argument of `MarkupLanguage.get_markup(text)`,
        as it is much more verbose.

        Args:
            text: The ANSI-text to prettify.

        Returns:
            The prettified ANSI text. This text's styles remain valid,
            so copy-pasting the argument into a command (like printf)
            that can show styled text will work the same way.
        """

        out = ""
        sequences = ""
        for token in self.tokenize_ansi(text):
            if token.ttype is TokenType.PLAIN:
                assert isinstance(token.data, str)
                out += token.data
                continue

            assert token.sequence is not None
            out += "\x1b[0m" + token.sequence + token.sequence.replace("\x1b", "\\x1b")
            sequences += token.sequence
            out += sequences

        return out

    def prettify_markup(self, text: str) -> str:
        """Returns a prettified (syntax-highlighted) markup str.

        Args:
            text: The markup-text to prettify.

        Returns:
            Prettified markup. This markup, excluding its styles,
            remains valid markup.
        """

        def _apply_macros(text: str) -> str:
            """Apply current macros to text"""

            for _, (method, args) in applied_macros:
                text = method(*args, text)

            return text

        def _pop_macro(name: str) -> None:
            """Pops a macro from applied_macros."""

            for i, (macro_name, _) in enumerate(applied_macros):
                if macro_name == name:
                    applied_macros.pop(i)
                    break

        styles: dict[TokenType, str] = {
            TokenType.MACRO: "210",
            TokenType.ESCAPED: "210 bold",
            TokenType.UNSETTER: "strikethrough",
        }

        applied_macros: list[tuple[str, MacroCall]] = []

        out = ""
        in_sequence = False
        current_styles: list[Token] = []

        for token in self.tokenize_markup(text):
            if token.ttype in [TokenType.PLAIN, TokenType.ESCAPED]:
                if in_sequence:
                    out += "]"

                in_sequence = False
                sequence = ""
                for style in current_styles:
                    if style.sequence is None:
                        continue

                    sequence += style.sequence

                out += sequence + _apply_macros(token.name) + "\033[0m"
                continue

            out += " " if in_sequence else "["
            in_sequence = True

            if token.ttype is TokenType.UNSETTER:
                name = token.name[1:]

                if name in self.macros:
                    _pop_macro(name)

                current_styles.append(token)

                special_style = (
                    name + " " if name in self.tags or name in self.user_tags else ""
                )
                out += self.parse(
                    f"/[{special_style}{styles[TokenType.UNSETTER]}]{name}"
                )
                continue

            if token.ttype is TokenType.MACRO:
                assert isinstance(token.data, tuple)

                name = token.name
                if "(" in name:
                    name = name[: token.name.index("(")]

                applied_macros.append((name, token.data))

                try:
                    out += token.data[0](*token.data[1], token.name)
                    continue

                except TypeError:  # Not enough arguments
                    pass

            if token.sequence is not None:
                current_styles.append(token)

            style_markup = styles.get(token.ttype) or token.name
            out += self.parse(f"[{style_markup}]{token.name}")

        if in_sequence:
            out += "]"

        return out + "[/]"


def main() -> None:
    """Main method"""

    parser = ArgumentParser()

    markup_group = parser.add_argument_group("Markup->ANSI")
    markup_group.add_argument(
        "-p", "--parse", metavar=("TXT"), help="parse a markup text"
    )
    markup_group.add_argument(
        "-e", "--escape", help="escape parsed markup", action="store_true"
    )
    # markup_group.add_argument(
    # "-o",
    # "--optimize",
    # help="set optimization level for markup parsing",
    # action="count",
    # default=0,
    # )

    markup_group.add_argument("--alias", action="append", help="alias src=dst")

    ansi_group = parser.add_argument_group("ANSI->Markup")
    ansi_group.add_argument(
        "-m", "--markup", metavar=("TXT"), help="get markup from ANSI text"
    )
    ansi_group.add_argument(
        "-s",
        "--show-inverse",
        action="store_true",
        help="show result of parsing result markup",
    )

    args = parser.parse_args()

    lang = MarkupLanguage()

    if args.markup:
        markup_text = lang.get_markup(args.markup)
        print(markup_text, end="")

        if args.show_inverse:
            print("->", lang.parse(markup_text))
        else:
            print()

    if args.parse:
        if args.alias:
            for alias in args.alias:
                src, dest = alias.split("=")
                lang.alias(src, dest)

        parsed = lang.parse(args.parse)

        if args.escape:
            print(ascii(parsed))
        else:
            print(parsed)

        return


tim = markup = MarkupLanguage()
"""The default TIM instances."""

if __name__ == "__main__":
    main()
