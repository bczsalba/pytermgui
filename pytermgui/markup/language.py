from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Callable

from ..colors import ColorSyntaxError, str_to_color
from ..regex import RE_MACRO
from ..terminal import terminal
from .aliases import apply_default_aliases
from .macros import apply_default_macros
from .parsing import (
    PARSERS,
    ContextDict,
    eval_alias,
    parse,
    tokenize_ansi,
    tokenize_markup,
    tokens_to_markup,
)

__all__ = [
    "MarkupLanguage",
    "StyledText",
    "tim",
]


class MarkupLanguage:
    def __init__(
        self, *, default_aliases: bool = True, default_macros: bool = True
    ) -> None:
        self._cache = {}

        self.context = ContextDict.create()
        self._aliases = self.context["aliases"]
        self._macros = self.context["macros"]

        if default_aliases:
            apply_default_aliases(self)

        if default_macros:
            apply_default_macros(self)

    @property
    def aliases(self) -> dict[str, str]:
        return self._aliases.copy()

    @property
    def macros(self) -> dict[str, Callable[[str, ...]]]:
        return self._macros.copy()

    def define(self, name: str, method: Callable[[str, ...], str]) -> None:
        if not name.startswith("!"):
            name = f"!{name}"

        self._macros[name] = method

    def alias(self, name: str, value: str, *, generate_unsetter: bool = True) -> None:
        value = eval_alias(value, self.context)

        def _generate_unsetter() -> str:
            unsetter = ""
            for tag in value.split():
                if tag in self._aliases or tag in self._macros:
                    unsetter += f" /{tag}"
                    continue

                try:
                    color = str_to_color(tag)
                    unsetter += f" /{'bg' if color.background else 'fg'}"

                except ColorSyntaxError:
                    unsetter += f" /{tag}"

            return unsetter.lstrip(" ")

        self._aliases[name] = value

        if generate_unsetter:
            self._aliases[f"/{name}"] = _generate_unsetter()

    def alias_multiple(
        self, *, generate_unsetter: bool = True, **items: dict[str, str]
    ) -> None:
        for name, value in items.items():
            self.alias(name, value, generate_unsetter=generate_unsetter)

    def parse(
        self,
        text: str,
        optimize: bool = False,
        append_reset: bool = True,
    ) -> str:

        key = (text, optimize, append_reset)

        can_cache = key in self._cache
        if "!" in text and RE_MACRO.match(text) is not None:
            can_cache = False

        if can_cache:
            return self._cache[key]

        output = parse(
            text,
            optimize=optimize,
            append_reset=append_reset,
            context=self.context,
        )

        self._cache[key] = output

        return output

    # TODO: This should be deprecated.
    def get_markup(self, text: str) -> str:
        return tokens_to_markup(tokenize_ansi(text))

    # TODO: This should be deprecated.
    def get_styled_plains(self, text: str) -> Generator[StyledText, None, None]:
        yield from StyledText.yield_from_ansi(text)

    def print(
        self,
        *items,
        sep: str = " ",
        end: str = "\n",
        flush: bool = True,
        file: StringIO = terminal,
    ) -> None:
        buff = []
        for item in items:
            buff.append(self.parse(item))

        file.write(sep.join(buff) + end)

        if flush:
            file.flush()


tim = MarkupLanguage()


@dataclass(frozen=True)
class StyledText:
    """An ANSI style-infused string.

    This is a sort of helper to handle ANSI texts in a more semantic manner. It
    keeps track of a sequence and a plain part.

    Calling `len()` will return the length of the printable, non-ANSI part, and
    indexing will return the characters at the given slice, but also include the
    sequences that are applied to them.

    To generate StyledText-s, it is recommended to use the `StyledText.yield_from_ansi`
    classmethod.
    """

    __slots__ = ("value", "sequences")

    sequences: str
    value: str

    @classmethod
    def yield_from_ansi(self, text: str) -> Generator[StyledText, None, None]:
        """Yields StyledTexts from an ANSI coded string.

        A new StyledText will be created each time a non-plain token follows a
        plain token, thus all texts will represent a single (ANSI)PLAIN group
        of characters.
        """

        parsers = PARSERS

        def _parse(token: Token) -> str:
            return parsers[type(token)](token, {})

        tokens = []

        for token in tokenize_ansi(text):
            if token.is_plain():
                yield StyledText(token.value, "".join(_parse(tkn) for tkn in tokens))
                tokens = []
                continue

            tokens.append(token)

    def __len__(self) -> int:
        return len(self.value)

    def __str__(self) -> str:
        return self.sequences + self.value

    def __getitem__(self, sli: int | slice) -> str:
        return self.sequences + self.value[sli]
