"""
A custom markup language to make styling `Widget`-s easier, and, well, more stylish.

Markup Syntax
=============

Basics
------
- Everything inside [square_brackets] is considered a tag
- Everything outside is considered a PLAIN text

Tag types
---------
- Style tags use the english name of the style (e.g. `[bold]`)

- Color tags can be of three types:
    + 8BIT: `[141]`
    + 24BIT/RGB: `[22;3;243]`
    + 24BIT/HEX: `[#2203FA]`
    + 24BIT colors are parsed as the same token type.

- Color tags set background when using the @ prefix: `[@141]`

- Macros are denoted by `!` prefix, and optional `(argument:list)` suffix

Macros
------

- Macros in markup convert from `[!name(arg1:arg2)]` to `name(arg1, arg2, text)`
- The next PLAIN token is always passed to the macro as its last argument
- The argument list is optional if a macro doesn't take any additional arguments
- A macro can be defined by using `MarkupLanguage.define(name, callable)`

Aliases
-------

- Tag aliases can be defined using `MarkupLanguage.alias(src, dst)`
- These are expanded in parse-time, and are recognized as regular style tokens
- Whenever an alias is defined, any cached markup containing it is removed

Caching
-------

- This module provides (opt-out) caching for parsed markup
- After parsing a previously unknown string, it is stored in `MarkupLanguage._cache`
- Next time the parser sees this markup string, it will restore the cached value
- Alias definitions delete affected cache entries

Instancing
----------

- `pytermgui` provides the `markup` name, which acts as the module-level language instance
- You can create your own instance using the `MarkupLanguage` name
- Each instance has its own tags, user tags & macros
- You might want a system-level and user-level instance when users can freely input markup

Usage
-----

- `MarkupLanguage.parse()`: Parse markup text into ANSI string
- `MarkupLanguage.get_markup()`: Get markup string from ANSI text
- `MarkupLanguage.tokenize_ansi()`, `MarkupLanguage.tokenize_markup()`: Tokenize text
- `MarkupLanguage.define()`: Define an instance-local macro
- `MarkupLanguage.alias()`: Define an instance-local alias

"""
from __future__ import annotations

import re
from random import shuffle
from dataclasses import dataclass
from argparse import ArgumentParser
from enum import Enum, auto as _auto
from typing import Iterator, Callable, Tuple, List

from .ansi_interface import foreground
from .exceptions import MarkupSyntaxError, AnsiSyntaxError


__all__ = ["MacroCallable", "MacroCall", "MarkupLanguage", "StyledText", "markup"]

MacroCallable = Callable[..., str]
MacroCall = Tuple[MacroCallable, List[str]]

RE_ANSI = re.compile(r"(?:\x1b\[(.*?)m)|(?:\x1b\](.*?)\x1b\\)")
RE_MACRO = re.compile(r"(![a-z0-9_]+)(?:\(([\w\/\.?=:]+)\))?")
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


def _macro_align(width: str, alignment: str, content: str) -> str:
    """Align text using fstring magic"""

    aligner = "<" if alignment == "left" else (">" if alignment == "right" else "^")
    return f"{content:{aligner}{width}}"


def _macro_expand(lang: MarkupLanguage, tag: str) -> str:
    """Expand tag alias"""

    if not tag in lang.user_tags:
        return tag

    return lang.get_markup("\x1b[" + lang.user_tags[tag] + "m ")[:-1]


def _macro_strip_fg(item: str) -> str:
    """Strip foreground color from item"""

    return markup.parse("[/fg]" + item)


def _macro_strip_bg(item: str) -> str:
    """Strip foreground color from item"""

    return markup.parse("[/bg]" + item)


def _macro_shuffle(item: str) -> str:
    """Shuffle a string using shuffle.shuffle on its list cast"""

    shuffled = list(item)
    shuffle(shuffled)

    return "".join(shuffled)


def _macro_link(*args) -> str:
    """Creates a clickable hyperlink.

    Note:
        Since this is a pretty new feature, its support is limited.
    """

    *uri_parts, label = args
    uri = ":".join(uri_parts)

    return f"\x1b]8;;{uri}\x1b\\{label}\x1b]8;;\x1b\\"


class TokenType(Enum):
    """An Enum to store various token types"""

    PLAIN = _auto()
    STYLE = _auto()
    MACRO = _auto()
    ESCAPED = _auto()
    FG_8BIT = _auto()
    BG_8BIT = _auto()
    FG_24BIT = _auto()
    BG_24BIT = _auto()
    UNSETTER = _auto()


@dataclass
class Token:
    """A class holding information on a singular Markup/ANSI unit"""

    ttype: TokenType
    data: str | MacroCall | None
    name: str = "<unnamed-token>"

    def __post_init__(self) -> None:
        """Set name to data if not provided"""

        if self.name == "<unnamed-token>":
            assert isinstance(self.data, str)
            self.name = self.data

    def __eq__(self, other: object) -> bool:
        """Check equality with `other`"""

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
        """Get ANSI sequence representing token"""

        if self.data is None:
            return None

        if self.ttype in [TokenType.PLAIN, TokenType.MACRO, TokenType.ESCAPED]:
            return None

        assert isinstance(self.data, str)

        if self.ttype in [TokenType.STYLE, TokenType.UNSETTER]:
            return "\033[" + self.data + "m"

        # Handle colors
        if self.ttype.name.startswith("BG"):
            template = "\x1b[48;{c_id};" + self.data + "m"
        else:
            template = "\x1b[38;{c_id};" + self.data + "m"

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

                    return plain_chars + styled_chars

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

    It holds data on default & custom tags and macros.

    It offers tokenizer methods for both `markup` and `ANSI` text,
    which can then be used to convert between the two formats.

    You can define macros using `MarkupLanguage.define`, and alias
    a set of tags using `MarkupLanguage.alias`.

    Parsing `markup` into `ANSI` text is done using the `parse()` method,
    where `optimizer_level` sets the amount of optimization that should be
    done on the result string.

    Getting `markup` from `ANSI` is done using the `get_markup()` method. Note
    that this method is "lossy": it does not preserve information about macros,
    and turns aliases into their underlying values.

    You can also use a `MarkupLanguage` instance as a context manager, which
    returns a callable with the signature of print that will parse every argument
    given to it, and pass through all **kwargs.

    ```python3
    import pytermgui as ptg

    ptg.markup.alias("my-tag", "@152 72 bold")
    with ptg.markup as mprint:
        mprint("This is [my-tag]my-tag[/]!")
    ```

    <p style="text-align: center">
        <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/parser.png
        style="width: 80%">
    </p>
    """

    def __init__(self, default_macros: bool = True) -> None:
        """Initialize object"""

        self.tags: dict[str, str] = STYLE_MAP.copy()
        self._cache: dict[str, StyledText] = {}
        self.macros: dict[str, MacroCallable] = {}
        self.user_tags: dict[str, str] = {}
        self.unsetters: dict[str, str | None] = UNSETTER_MAP.copy()

        self.should_cache: bool = True

        if default_macros:
            self.define("!link", _macro_link)
            self.define("!align", _macro_align)
            self.define("!markup", self.get_markup)
            self.define("!shuffle", _macro_shuffle)
            self.define("!strip_bg", _macro_strip_bg)
            self.define("!strip_fg", _macro_strip_fg)
            self.define("!upper", lambda item: str(item.upper()))
            self.define("!lower", lambda item: str(item.lower()))
            self.define("!title", lambda item: str(item.title()))
            self.define("!capitalize", lambda item: str(item.capitalize()))
            self.define("!expand", lambda tag: _macro_expand(self, tag))

    @staticmethod
    def _get_color_token(tag: str) -> Token | None:
        """Try to get color token from a tag"""

        def _hex_to_rgb(color: str) -> str:
            """Get rgb color from hex"""

            return ";".join(str(int(color[i : i + 2], 16)) for i in (0, 2, 4))

        background = tag.startswith("@")
        if tag.startswith("@"):
            tag = tag[1:]

        if tag in foreground.names:
            return Token(
                name=tag,
                ttype=(TokenType.BG_8BIT if background else TokenType.FG_8BIT),
                data=str(foreground.names[tag]),
            )

        data_256 = RE_256.match(tag)
        if data_256 is not None:
            return Token(
                name=tag,
                ttype=(TokenType.BG_8BIT if background else TokenType.FG_8BIT),
                data=tag,
            )

        data_hex = RE_HEX.match(tag)
        if data_hex is not None:
            return Token(
                name=tag,
                ttype=(TokenType.BG_24BIT if background else TokenType.FG_24BIT),
                data=_hex_to_rgb(tag[1:]),
            )

        data_rgb = RE_RGB.match(tag)
        if data_rgb is not None:
            return Token(
                name=tag,
                ttype=(TokenType.BG_24BIT if background else TokenType.FG_24BIT),
                data=tag,
            )

        return None

    def __enter__(self) -> Callable[..., None]:
        """Return a print method that parses markup"""

        def printer(*args, **kwargs) -> None:
            """Parse all arguments and pass them through to print, along with kwargs"""

            parsed = []
            for arg in args:
                parsed.append(self.parse(str(arg)))

            print(*parsed, **kwargs)

        return printer

    def __exit__(self, _, exception: Exception, __) -> None:
        """Raise any exception that happened in context"""

        if exception is not None:
            raise exception

    def tokenize_markup(self, markup_text: str) -> Iterator[Token]:
        """Tokenize markup text, return an Iterator to save memory"""

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
                if tag in self.unsetters:
                    yield Token(
                        name=tag, ttype=TokenType.UNSETTER, data=self.unsetters[tag]
                    )

                elif tag in self.user_tags:
                    yield Token(
                        name=tag, ttype=TokenType.STYLE, data=self.user_tags[tag]
                    )

                elif tag in self.tags:
                    yield Token(name=tag, ttype=TokenType.STYLE, data=self.tags[tag])

                # Try to find a color token
                else:
                    color_token = self._get_color_token(tag)
                    if color_token is not None:
                        yield color_token
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
        """Tokenize ansi text, return an Iterator to save memory."""

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
                    # name = "@" + name # <- This broke line_break, but might be needed
                    types = [TokenType.BG_8BIT, TokenType.BG_24BIT]

                ttype = types[0] if parts[1] == "5" else types[1]

                yield Token(ttype=ttype, data=name)

            cursor = end

        if cursor < len(ansi):
            plain = ansi[cursor:]

            yield Token(ttype=TokenType.PLAIN, data=plain)

    def define(self, name: str, method: MacroCallable) -> None:
        """Define a Macro tag that executes `method`

        The `!` prefix is added to the name if not there already."""

        if not name.startswith("!"):
            name = "!" + name

        self.macros[name] = method
        self.unsetters["/" + name] = None

    def alias(self, name: str, value: str) -> None:
        """Alias a markup tag to stand for some value, generate unsetter for it"""

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
            self.unsetters["/" + name] = value
            self.user_tags[name] = value
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

    def parse(self, markup_text: str) -> StyledText:
        """Parse markup"""

        # TODO: Add more optimizations:
        #       - keep track of currently-active tokens
        #       - clean up widget dump

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

        # TODO: Macros are only ran once with caching enabled
        if self.should_cache and markup_text in self._cache:
            return self._cache[markup_text]

        for token in self.tokenize_markup(markup_text):
            if sequence != "" and previous_token == token:
                continue

            if token.ttype == TokenType.UNSETTER and token.data == "0":
                out += "\033[0m"
                sequence = ""
                continue

            previous_token = token

            if token.ttype is TokenType.MACRO:
                assert isinstance(token.data, tuple)

                applied_macros.append((token.name, token.data))
                continue

            if token.data == "<macro>" and token.ttype is TokenType.UNSETTER:
                for call_str, data in applied_macros:
                    macro_match = RE_MACRO.match(call_str)
                    assert macro_match is not None

                    macro_name = macro_match.groups()[0]

                    if "/" + macro_name == token.name:
                        applied_macros.remove((call_str, data))

                continue

            if token.sequence is None:
                if previous_sequence == sequence:
                    out += _apply_macros(token.name)
                    continue

                previous_sequence = sequence

                out += sequence + _apply_macros(token.name)
                sequence = ""

            else:
                sequence += token.sequence

        if sequence + previous_sequence != "":
            out += "\x1b[0m"

        out = StyledText(out)
        self._cache[markup_text] = out
        return out

    def get_markup(self, ansi: str) -> str:
        """Get markup from ANSI text"""

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


markup = MarkupLanguage()

if __name__ == "__main__":
    main()
