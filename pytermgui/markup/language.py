"""Wrappers around the TIM parsing engine, implementing caching and context management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from typing import Callable, Generator, Iterator, Match

from ..colors import Color, ColorSyntaxError, str_to_color
from ..regex import RE_MARKUP
from ..term import get_terminal
from .aliases import apply_default_aliases
from .macros import apply_default_macros
from .parsing import (
    PARSERS,
    ContextDict,
    MacroType,
    create_context_dict,
    eval_alias,
    parse_tokens,
    tokenize_ansi,
    tokenize_markup,
    tokens_to_markup,
)
from .style_maps import CLEARERS
from .tokens import Token

STRICT_MARKUP = bool(os.getenv("PTG_STRICT_MARKUP"))

__all__ = [
    "escape",
    "MarkupLanguage",
    "StyledText",
    "tim",
]

Tokenizer = Callable[[str], Iterator[Token]]


def escape(text: str) -> str:
    """Escapes any markup found within the given text."""

    def _repl(matchobj: Match) -> str:
        full, *_ = matchobj.groups()

        return f"\\{full}"

    return RE_MARKUP.sub(_repl, text)


class MarkupLanguage:
    """A relatively simple object that binds context to TIM parsing functions.

    Most of the job this class has is to pass along a `ContextDict` to various
    "lower level" functions, in order to maintain a sort of state. It also exposes
    ways to modify this state, namely the `alias` and `define` methods.
    """

    def __init__(
        self,
        *,
        strict: bool = False,
        default_aliases: bool = True,
        default_macros: bool = True,
    ) -> None:
        self._cache: dict[tuple[str, bool, bool], tuple[str, list[Token], bool]] = {}

        self.context = create_context_dict()
        self._aliases = self.context["aliases"]
        self._macros = self.context["macros"]

        if default_aliases:
            apply_default_aliases(self)

        if default_macros:
            apply_default_macros(self)

        self.strict = strict or STRICT_MARKUP

    @property
    def aliases(self) -> dict[str, str]:
        """Returns a copy of the aliases defined in context."""

        return self._aliases.copy()

    @property
    def macros(self) -> dict[str, MacroType]:
        """Returns a copy of the macros defined in context."""

        return self._macros.copy()

    def clear_cache(self) -> None:
        """Clears the internal cache.

        Use this after re-defining aliases.
        """

        self._cache.clear()

    def define(self, name: str, method: MacroType) -> None:
        """Defines a markup macro.

        Macros are essentially function bindings callable within markup. They can be
        very useful to represent changing data and simplify TIM code.

        Args:
            name: The name that will be used within TIM to call the macro. Must start with
                a bang (`!`).
            method: The function bound to the name given above. This function will take
                any number of strings as arguments, and return a terminal-ready (i.e. parsed)
                string.
        """

        if not name.startswith("!"):
            raise ValueError("TIM macro names must be prefixed by `!`.")

        self._macros[name] = method

    def alias(self, name: str, value: str, *, generate_unsetter: bool = True) -> None:
        """Creates an alias from one custom name to a set of styles.

        These can be used to store and reference a set of tags using only one name.

        Aliases may reference other aliases, but only do this consciously, as it can become
        a hard to follow trail of sorrow very quickly!

        Args:
            name: The name this alias will be referenced by.
            value: The markup value that the alias will represent.
            generate_unsetter: Disable generating clearer aliases.

                For example:
                    ```
                    my-tag = 141 bold italic
                    ```

                will generate:
                    ```
                    /my-tag = /fg /bold /italic
                    ```
        """

        def _generate_unsetter() -> str:
            unsetter = ""
            no_alias = eval_alias(value, self.context)

            for tag in no_alias.split():
                if "(" in tag and ")" in tag:
                    tag = tag[: tag.find("(")]

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

    def alias_multiple(self, *, generate_unsetter: bool = True, **items: str) -> None:
        """Runs `MarkupLanguage.alias` repeatedly for all arguments.

        The same `generate_unsetter` value will be used for all calls.

        You can use this in two forms:

        - Traditional keyword arguments:

            ```python
            lang.alias_multiple(my-tag1="bold", my-tag2="italic")
            ```

        - Keyword argument unpacking:

            ```python
            my_aliases = {"my-tag1": "bold", "my-tag2": "italic"}
            lang.alias_multiple(**my_aliases)
            ```
        """

        for name, value in items.items():
            self.alias(name, value, generate_unsetter=generate_unsetter)

    def parse(
        self,
        text: str,
        optimize: bool = False,
        append_reset: bool = True,
    ) -> str:
        """Parses some markup text.

        This is a thin wrapper around [markup.parsing.parse](/reference/
        pytermgui/markup/parsing#pytermgui.markup.parsing.parse). The main additions
        of this wrapper are a caching system, as well as state management.

        Ignoring caching, all calls to this function would be equivalent to:

        ```python3
        def parse(self, *args, **kwargs) -> str:
            kwargs["context"] = self.context

            return parse(*args, **kwargs)
        ```
        """

        key = (text, optimize, append_reset)

        cache_hit = self._cache.get(key)
        if cache_hit is not None:
            cached, tokens, has_macro = cache_hit

            # Re-parse using known tokens when macro is present
            #
            # This saves a tiny fraction of time (around 0.2ms) when parsing
            # macros, for a loss of an even smaller time for the general,
            # non-macro usecase.
            if has_macro:
                output = parse_tokens(
                    tokens,
                    optimize=optimize,
                    append_reset=append_reset,
                    context=self.context,
                    ignore_unknown_tags=not self.strict,
                )

                return output

            return cached

        tokens = list(tokenize_markup(text))

        output = parse_tokens(
            tokens,
            optimize=optimize,
            append_reset=append_reset,
            context=self.context,
            ignore_unknown_tags=not self.strict,
        )

        has_macro = any(token.is_macro() for token in tokens)

        self._cache[key] = (output, tokens, has_macro)

        return output

    # TODO: This should be deprecated.
    @staticmethod
    def get_markup(text: str) -> str:
        """DEPRECATED: Convert ANSI text into markup.

        This function does not use context, and thus is out of place here.
        """

        return tokens_to_markup(list(tokenize_ansi(text)))

    def group_styles(
        self, text: str, tokenizer: Tokenizer = tokenize_ansi
    ) -> Generator[StyledText, None, None]:
        """Generate StyledText-s from some text, using our context.

        See `StyledText.group_styles` for arguments.
        """

        yield from StyledText.group_styles(
            text, tokenizer=tokenizer, context=self.context
        )

    def print(self, *args, **kwargs) -> None:
        """Parse all arguments and pass them through to print, along with kwargs."""

        parsed = []
        for arg in args:
            parsed.append(self.parse(str(arg)))

        get_terminal().print(*parsed, **kwargs)


tim = MarkupLanguage()


@dataclass(frozen=True)
class StyledText:
    """An ANSI style-infused string.

    This is a sort of helper to handle ANSI texts in a more semantic manner. It
    keeps track of a sequence and a plain part.

    Calling `len()` will return the length of the printable, non-ANSI part, and
    indexing will return the characters at the given slice, but also include the
    sequences that are applied to them.

    To generate StyledText-s, it is recommended to use the `StyledText.group_styles`
    classmethod.
    """

    __slots__ = ("plain", "sequences", "tokens", "link", "__dict__")

    sequences: str
    plain: str
    tokens: list[Token]
    link: str | None

    @cached_property
    def foreground(self) -> Color | None:
        """Returns the foreground color of this object."""

        colors = [
            tkn
            for tkn in self.tokens
            if Token.is_color(tkn) and not tkn.color.background
        ]

        if len(colors) == 0:
            return None

        return colors[-1].color

    @cached_property
    def background(self) -> Color | None:
        """Returns the background color of this object."""

        colors = [
            tkn for tkn in self.tokens if Token.is_color(tkn) and tkn.color.background
        ]

        if len(colors) == 0:
            return None

        return colors[-1].color

    @cached_property
    def bold(self) -> bool:
        """Returns this text is bold."""

        return any(Token.is_style(tkn) and tkn.markup == "bold" for tkn in self.tokens)

    @cached_property
    def dim(self) -> bool:
        """Returns this text is dimmed."""

        return any(Token.is_style(tkn) and tkn.markup == "dim" for tkn in self.tokens)

    @cached_property
    def italic(self) -> bool:
        """Returns this text is italicized."""

        return any(
            Token.is_style(tkn) and tkn.markup == "italic" for tkn in self.tokens
        )

    @cached_property
    def underline(self) -> bool:
        """Returns this text is underlined."""

        return any(
            Token.is_style(tkn) and tkn.markup == "underline" for tkn in self.tokens
        )

    @cached_property
    def blink(self) -> bool:
        """Returns this text is blinking."""

        return any(Token.is_style(tkn) and tkn.markup == "blink" for tkn in self.tokens)

    @cached_property
    def blink2(self) -> bool:
        """Returns this text is alternate-blinking."""

        return any(
            Token.is_style(tkn) and tkn.markup == "blink2" for tkn in self.tokens
        )

    @cached_property
    def strikethrough(self) -> bool:
        """Returns this text is striked out."""

        return any(
            Token.is_style(tkn) and tkn.markup == "strikethrough" for tkn in self.tokens
        )

    @cached_property
    def inverse(self) -> bool:
        """Returns this text has its colors inversed."""

        return any(
            Token.is_style(tkn) and tkn.markup == "inverse" for tkn in self.tokens
        )

    @cached_property
    def overline(self) -> bool:
        """Returns this text is overlined."""

        return any(
            Token.is_style(tkn) and tkn.markup == "overline" for tkn in self.tokens
        )

    @staticmethod
    def group_styles(
        text: str,
        tokenizer: Tokenizer = tokenize_ansi,
        context: ContextDict | None = None,
    ) -> Generator[StyledText, None, None]:
        """Yields StyledTexts from an ANSI coded string.

        A new StyledText will be created each time a non-plain token follows a
        plain token, thus all texts will represent a single (ANSI)PLAIN group
        of characters.
        """

        context = context if context is not None else create_context_dict()

        parsers = PARSERS
        link = None

        def _parse(token: Token) -> str:
            nonlocal link

            if token.is_macro():
                return token.markup

            if token.is_hyperlink():
                link = token
                return ""

            if link is not None and Token.is_clear(token) and token.targets(link):
                link = None

            if token.is_clear() and token.value not in CLEARERS:
                return token.markup

            # The full text (last arg) is not relevant here, as ANSI parsing doesn't
            # use any context-defined tags, so no errors will occur.
            return parsers[type(token)](token, context, lambda: "")  # type: ignore

        tokens: list[Token] = []
        token: Token

        for token in tokenizer(text):
            if token.is_plain():
                yield StyledText(
                    "".join(_parse(tkn) for tkn in tokens),
                    token.value,
                    tokens + [token],
                    link.value if link is not None else None,
                )

                tokens = [tkn for tkn in tokens if not tkn.is_cursor()]
                continue

            if Token.is_clear(token):
                tokens = [tkn for tkn in tokens if not token.targets(tkn)]

                if len(tokens) > 0 and tokens[-1] == token:
                    continue

            if len(tokens) > 0 and all(tkn.is_clear() for tkn in tokens):
                tokens = []

            tokens.append(token)

        # if len(tokens) > 0:
        #     token = PlainToken("")

        #     yield StyledText(
        #         "".join(_parse(tkn) for tkn in tokens),
        #         token.value,
        #         tokens + [token],
        #         link.value if link is not None else None,
        #     )

    @classmethod
    def first_of(cls, text: str) -> StyledText | None:
        """Returns the first element of cls.group_styles(text)."""

        for item in cls.group_styles(text):
            return item

        return None

    def __len__(self) -> int:
        return len(self.plain)

    def __str__(self) -> str:
        return self.sequences + self.plain

    def __getitem__(self, sli: int | slice) -> str:
        return self.sequences + self.plain[sli]
