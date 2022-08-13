"""This module provides the `Highlighter` class, and some pre-configured instances."""

from __future__ import annotations

import builtins
import keyword
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Callable, Generator, Match, Pattern, Protocol

from .markup import Token, consume_tag
from .regex import RE_MARKUP

if TYPE_CHECKING:
    from .fancy_repr import FancyYield

__all__ = [
    "Highlighter",
    "RegexHighlighter",
    "highlight_tim",
    "highlight_python",
]


class Highlighter(Protocol):  # pylint: disable=too-few-public-methods
    """The protocol for highlighters."""

    def __call__(self, text: str, cache: bool = True) -> str:
        """Highlights the given text.

        Args:
            text: The text to highlight.
            cache: If set (default), results will be stored, keyed by their respective
                inputs, and retrieved the next time the same key is given.
        """


@dataclass
class RegexHighlighter:
    """A class to highlight strings using regular expressions.

    This class must be provided with a list of styles. These styles are really just a
    tuple of the markup alias name, and their associated RE patterns. If *all* aliases
    in the instance use the same prefix, it can be given under the `prefix` key and
    ommitted from the style names.

    On construction, the instance will combine all of its patterns into a monster regex
    including named capturing groups. The general format is something like:

        (?P<{name1}>{pattern1})|(?P<{name2}>{pattern2})|...

    Calling this instance will then replace all matches, going in the order of
    definition, with style-injected versions. These follow the format:

        [{prefix?}{name}]{content}[/{prefix}{name}]

    Oddities to keep in mind:
    - Regex replace goes in the order of the defined groups, and is non-overlapping. Two
        groups cannot match the same text.
    - Because of how capturing groups work, everything within the patterns will be
        matched. To look for context around a match, look-around assertions can be used.
    """

    styles: list[tuple[str, str]]
    """A list of tuples of (style_alias, pattern_str)."""

    prefix: str = ""
    """Some string to insert before each style alias."""

    pre_formatter: Callable[[str], str] | None = None
    """A callable that formats the input string, before any highlighting is done to it."""

    match_formatter: Callable[[Match, str], str] | None = None
    """A callable of (match, content) that gets called on every match.

    Its return value will be used as the content that the already set highlighting will apply
    to. Useful to trim text, or apply other transformations before inserting it back.
    """

    re_flags: int = 0
    """All regex flags to apply when compiling the generated pattern, OR-d (|) together."""

    _pattern: Pattern = field(init=False)
    _highlight_cache: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Combines all styles into one pattern."""

        pattern = ""
        names: list[str] = []
        for name, ptrn in self.styles:
            pattern += f"(?P<{name}>{ptrn})|"
            names.append(name)

        pattern = pattern[:-1]

        self._pattern = re.compile(pattern, flags=self.re_flags)

    def __call__(self, text: str, cache: bool = True) -> str:
        """Highlights the given text, using the combined regex pattern."""

        if self.pre_formatter is not None:
            text = self.pre_formatter(text)

        if cache and text in self._highlight_cache:
            return self._highlight_cache[text]

        cache_key = text

        def _insert_style(matchobj: Match) -> str:
            """Returns the match inserted into a markup style."""

            groups = matchobj.groupdict()

            name = matchobj.lastgroup
            content = groups.get(str(name), None)

            if self.match_formatter is not None:
                content = self.match_formatter(matchobj, content)

                if content == "":
                    return ""

            tag = f"{self.prefix}{name}"
            style = f"[{tag}]{{}}[/{tag}]"

            return style.format(content)

        text = self._pattern.sub(_insert_style, text)
        self._highlight_cache[cache_key] = text

        return text

    def __fancy_repr__(self) -> Generator[FancyYield, None, None]:
        """Yields some fancy looking repr text."""

        preview = self("highlight_python()") + "\x1b[0m"
        pattern = self._pattern.pattern

        if len(pattern) > 40:
            pattern = pattern[:38] + "..."

        yield f"<{type(self).__name__} pattern: {pattern!r}, preview: "
        yield {"text": str(preview), "highlight": False}

        yield ">"


def highlight_tim(text: str, cache: bool = True) -> str:
    """Highlights some TIM code."""

    @lru_cache(1048)
    def _highlight(txt: str) -> str:
        output = ""
        cursor = 0
        active_tokens: list[Token] = []

        def _get_active_markup() -> str:
            active_markup = " ".join(tkn.markup for tkn in active_tokens)

            if active_markup == "":
                return ""

            return f"[{active_markup}]"

        for matchobj in RE_MARKUP.finditer(txt):
            start, end = matchobj.span()

            if cursor < start:
                if cursor > 0:
                    output += "]"

                output += _get_active_markup()
                output += f"{txt[cursor:start]}[/]"

            *_, tags = matchobj.groups()

            output += "["
            for tag in tags.split():
                token = consume_tag(tag)
                output += f"{token.prettified_markup} "

                if Token.is_clear(token):
                    active_tokens = [
                        tkn for tkn in active_tokens if not token.targets(tkn)
                    ]

                else:
                    active_tokens.append(token)

            output = output.rstrip()
            cursor = end

        if cursor < len(txt) - 1:
            if cursor > 0:
                output += "]"

            output += _get_active_markup()
            output += f"{txt[cursor:]}"

            if len(active_tokens) > 0:
                output += "[/]"

        if output.count("[") != output.count("]"):
            output += "]"

        return output

    if cache:
        return _highlight(text)

    return _highlight.__wrapped__(text)


_BUILTIN_NAMES = "|".join(f"(?:{item})" for item in dir(builtins))
_KEYWORD_NAMES = "|".join(
    f"(?:{keyw})" for keyw in list(keyword.kwlist) + ["builtin", "function", "module"]
)

highlight_python = RegexHighlighter(
    prefix="code.",
    styles=[
        ("multiline_str", r"([frbu]*)\"{3}([\s\S]*?)(?<!\\)\"{3}"),
        (
            "str",
            r"([frbu]*(\".*?(?<!\\)\")|(\'.*?(?<!\\)\'))",
        ),
        ("comment", "(#.*)"),
        ("keyword", rf"\b(?<![\.\-])()({_KEYWORD_NAMES}+)\b"),
        ("builtin", rf"\b(?<!\.)({_BUILTIN_NAMES})\b"),
        ("identifier", r"([^ \.=]+)(?=\()"),
        ("global", r"(?<=\b)([A-Z]\w+)"),
        ("number", r"(?<=\b)((?:0x[\da-zA-Z]+)|(?:\d+))"),
    ],
)
