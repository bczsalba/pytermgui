"""The internals of the TIM engine."""

from __future__ import annotations

import json
from typing import Callable, Iterator, Protocol, TypedDict
from warnings import filterwarnings, warn

from ..colors import Color
from ..exceptions import ColorSyntaxError, MarkupSyntaxError
from ..regex import RE_ANSI_NEW as RE_ANSI
from ..regex import RE_MACRO, RE_MARKUP, RE_POSITION
from .style_maps import CLEARERS, REVERSE_CLEARERS, REVERSE_STYLES, STYLES
from .tokens import (
    AliasToken,
    ClearToken,
    ColorToken,
    CursorToken,
    HLinkToken,
    MacroToken,
    PlainToken,
    PseudoToken,
    StyleToken,
    Token,
)

# TODO: Improve first-run performance.

filterwarnings("always")

STATE_COPY = "#stash"
STATE_CUT = "#stash/"

STATE_RESTORE = "#pop"
STATE_REPLACE = "#/pop"

LINK_TEMPLATE = "\x1b]8;;{uri}\x1b\\{label}\x1b]8;;\x1b\\"

STATE_PSEUDOS = [STATE_CUT, STATE_COPY, STATE_REPLACE, STATE_RESTORE]
PSEUDO_TOKENS = ["#auto", *STATE_PSEUDOS]

__all__ = [
    "ContextDict",
    "create_context_dict",
    "consume_tag",
    "tokenize_markup",
    "tokenize_ansi",
    "optimize_tokens",
    "optimize_markup",
    "tokens_to_markup",
    "get_markup",
    "parse",
    "parse_tokens",
]


class MacroType(Protocol):  # pylint: disable=too-few-public-methods
    """A protocol for TIM macros."""

    def __call__(  # pylint: disable=no-method-argument, no-self-argument
        *args: str,
    ) -> str:
        """Applies the macro."""


class ContextDict(TypedDict):
    """A dictionary to hold context about a markup language's environment.

    It has two sub-dicts:

    - aliases
    - macros

    For information about what they do and contain, see the
    [MarkupLanguage docs](/reference/pytermgui/markup/
    language#pytermgui.markup.language.MarkupLanguage).
    """

    aliases: dict[str, str]
    macros: dict[str, MacroType]


def create_context_dict() -> ContextDict:
    """Creates a new context dictionary, initializing its sub-dicts.

    Returns:
        A dictionary with `aliases` and `macros` defined as empty sub-dicts.
    """

    return {"aliases": {}, "macros": {}}


def consume_tag(tag: str) -> Token:  # pylint: disable=too-many-return-statements
    """Consumes a tag text, returns the associated Token."""

    if tag in STYLES:
        return StyleToken(tag)

    if tag.startswith("/"):
        return ClearToken(tag)

    if tag.startswith("!"):
        matchobj = RE_MACRO.match(tag)

        if matchobj is not None:
            name, args = matchobj.groups()

            if args is None:
                return MacroToken(name, tuple())

            return MacroToken(name, tuple(args.split(":")))

    if tag.startswith("~"):
        return HLinkToken(tag[1:])

    if tag.startswith("(") and tag.endswith(")"):
        values = tag[1:-1].split(";")
        if len(values) != 2:
            raise MarkupSyntaxError(
                tag,
                f"should have exactly 2 values separated by `;`, not {len(values)}",
                "",
            )

        return CursorToken(tag[1:-1], *map(int, values))

    if tag in PSEUDO_TOKENS:
        return PseudoToken(tag)

    token: Token
    try:
        token = ColorToken(tag, Color.parse(tag, localize=False))

    except ColorSyntaxError:
        token = AliasToken(tag)

    return token


def tokenize_markup(text: str) -> Iterator[Token]:
    """Converts some markup text into a stream of tokens.

    Args:
        text: Any valid markup.

    Yields:
        The generated tokens, in the order they occur within the markup.
    """

    cursor = 0
    length = len(text)
    has_inverse = False
    for matchobj in RE_MARKUP.finditer(text):
        full, escapes, content = matchobj.groups()
        start, end = matchobj.span()

        if cursor < start:
            yield PlainToken(text[cursor:start])

        if not escapes == "":
            _, remaining = divmod(len(escapes), 2)

            yield PlainToken(full[max(1 - remaining, 1) :])
            cursor = end

            continue

        for tag in content.split():
            if tag == "inverse":
                has_inverse = True

            if tag == "/inverse":
                has_inverse = False

            consumed = consume_tag(tag)
            if has_inverse:
                if consumed.markup == "/fg":
                    consumed = ClearToken("/fg")

                elif consumed.markup == "/bg":
                    consumed = ClearToken("/bg")

            yield consumed

        cursor = end

    if cursor < length:
        yield PlainToken(text[cursor:length])


def tokenize_ansi(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    text: str,
) -> Iterator[Token]:
    """Converts some ANSI-coded text into a stream of tokens.

    Args:
        text: Any valid ANSI-coded text.

    Yields:
        The generated tokens, in the order they occur within the text.
    """

    cursor = 0

    for matchobj in RE_ANSI.finditer(text):
        start, end = matchobj.span()

        csi = matchobj.groups()[0:2]
        link_osc = matchobj.groups()[2:4]

        if cursor < start:
            yield PlainToken(text[cursor:start])

        if link_osc != (None, None):
            cursor = end
            uri, label = link_osc

            yield HLinkToken(uri)
            yield PlainToken(label)
            yield ClearToken("/~")

            continue

        full, content = csi

        cursor = end

        code = ""

        # Position
        posmatch = RE_POSITION.match(full)

        if posmatch is not None:
            ypos, xpos = posmatch.groups()
            if not ypos and not xpos:
                raise ValueError(
                    f"Cannot parse cursor when no position is supplied. Match: {posmatch!r}"
                )

            yield CursorToken(content, int(ypos) or None, int(xpos) or None)
            continue

        parts = content.split(";")

        state = None
        color_code = ""
        for part in parts:
            if state is None:
                if part in REVERSE_STYLES:
                    yield StyleToken(REVERSE_STYLES[part])
                    continue

                if part in REVERSE_CLEARERS:
                    yield ClearToken(REVERSE_CLEARERS[part])
                    continue

                if part in ("38", "48"):
                    state = "COLOR"
                    color_code += part + ";"
                    continue

                # standard colors
                try:
                    yield ColorToken(part, Color.parse(part, localize=False))
                    continue

                except ColorSyntaxError as exc:
                    raise ValueError(f"Could not parse color tag {part!r}.") from exc

            if state != "COLOR":
                continue

            color_code += part + ";"

            # Ignore incomplete RGB colors
            if (
                color_code.startswith(("38;2;", "48;2;"))
                and len(color_code.split(";")) != 6
            ):
                continue

            try:
                code = color_code

                if code.startswith(("38;2;", "48;2;", "38;5;", "48;5;")):
                    stripped = code[5:-1]

                    if code.startswith("4"):
                        stripped = "@" + stripped

                    code = stripped

                yield ColorToken(code, Color.parse(code, localize=False))

            except ColorSyntaxError:
                continue

            state = None
            color_code = ""

    remaining = text[cursor:]
    if len(remaining) > 0:
        yield PlainToken(remaining)


def eval_alias(text: str, context: ContextDict) -> str:
    """Evaluates a space-delimited string of alias tags into their underlying value.

    Args:
        text: A space-separated string containing the aliases.

    Returns:
        The space-separated string that the input aliases represent.
    """

    aliases = context["aliases"]

    evaluated = ""
    for tag in text.split():
        if tag not in aliases:
            evaluated += tag + " "
            continue

        evaluated += eval_alias(aliases[tag], context) + " "

    return evaluated.rstrip(" ")


def parse_plain(token: PlainToken, _: ContextDict, __: Callable[[], str]) -> str:
    """Parses a plain token."""

    return token.value


def parse_color(token: ColorToken, _: ContextDict, __: Callable[[], str]) -> str:
    """Parses a color token."""

    return token.color.get_localized().sequence


def parse_style(token: StyleToken, _: ContextDict, __: Callable[[], str]) -> str:
    """Parses a style token."""

    index = STYLES[token.value]

    return f"\x1b[{index}m"


def parse_macro(
    token: MacroToken, context: ContextDict, get_full: Callable[[], str]
) -> tuple[MacroType, tuple[str, ...]]:
    """Parses a macro token.

    Returns:
        A tuple containing the callable bound to the name, as well as the arguments
        passed to it.
    """

    func = context["macros"].get(token.value)

    if func is None:
        dump = json.dumps(context["macros"], indent=2, default=str)

        raise MarkupSyntaxError(
            token.value, f"not defined in macro context: {dump}", get_full()
        )

    return func, token.arguments


def parse_alias(
    token: AliasToken, context: ContextDict, get_full: Callable[[], str]
) -> str:
    """Parses an alias token."""

    if token.value not in context["aliases"]:
        dump = json.dumps(context["aliases"], indent=2, default=str)

        raise MarkupSyntaxError(
            token.value, f"not defined in alias context: {dump}", get_full()
        )

    meaning = context["aliases"][token.value]

    return eval_alias(meaning, context).rstrip(" ")


def parse_clear(token: ClearToken, _: ContextDict, get_full: Callable[[], str]) -> str:
    """Parses a clearer token."""

    if token.value == "/~":
        return "\x1b]8;;\x1b\\"

    index = CLEARERS.get(token.value)
    if index is None:
        raise MarkupSyntaxError(
            token.value, "not a recognized clearer or alias", get_full()
        )

    return f"\x1b[{index}m"


def parse_cursor(token: CursorToken, _: ContextDict, __: Callable[[], str]) -> str:
    """Parses a cursor token."""

    ypos, xpos = map(lambda i: "" if i is None else i, token)

    return f"\x1b[{ypos};{xpos}H"


def parse_state_pseudo(
    token: PseudoToken,
    tokens: list[Token],
    index: int,
    save_state: list[Token],
    context: ContextDict,
) -> str:
    """Parses a state pseudo tokens"""

    tag = token.value

    parsed = ""

    if tag.startswith(STATE_CUT):
        save_state.clear()
        save_state.extend(filter(lambda tkn: not tkn.is_plain(), tokens[:index]))

        if not tag == STATE_COPY:
            parsed += "\x1b[0m"

    # Restore
    else:
        local_state = save_state.copy()

        if tag == STATE_REPLACE:
            local_state.insert(0, ClearToken("/"))

        parsed = parse_tokens(
            local_state,
            context=context,
            optimize=False,
            append_reset=False,
        )

    return parsed


def optimize_tokens(tokens: list[Token]) -> Iterator[Token]:
    """Optimizes a stream of tokens, only yielding functionally relevant ones.

    Args:
        tokens: Any list of Token objects. Usually obtained from `tokenize_markup`
            or `tokenize_ansi`.

    Yields:
        All those tokens within the input iterator that are functionally relevant,
            keeping their order.
    """

    previous: list[Token] = []
    current_tag_group: list[Token] = []

    def _diff_previous() -> Iterator[Token]:
        """Find difference from the previously active list of tokens."""

        applied = previous.copy()

        for tkn in current_tag_group:
            targets = []

            clearer = Token.is_clear(tkn)
            if Token.is_clear(tkn):
                targets = [tkn.targets(tag) for tag in applied]

            if tkn in previous and not clearer:
                continue

            if clearer and not any(targets):
                continue

            applied.append(tkn)
            yield tkn

    def _remove_redundant_color(token: Token) -> None:
        """Removes non-functional colors.

        These happen in the following ways:
        - Multiple colors of the same channel (fg/bg) are present.
        - A color is applied, then a clearer clears it.
        """

        for applied in current_tag_group.copy():
            if Token.is_clear(applied) and applied.targets(token):
                current_tag_group.remove(applied)

            if not Token.is_color(applied):
                continue

            old = applied.color

            if old.background == new.background:
                current_tag_group.remove(applied)

    for token in tokens:
        if Token.is_plain(token):
            yield from _diff_previous()
            yield token

            previous = current_tag_group.copy()

            continue

        if Token.is_color(token):
            new = token.color

            _remove_redundant_color(token)

            if not any(token.markup == applied.markup for applied in current_tag_group):
                current_tag_group.append(token)

            continue

        if token.is_style():
            if not any(token == tag for tag in current_tag_group):
                current_tag_group.append(token)

            continue

        if Token.is_clear(token):
            applied = False
            for tag in current_tag_group.copy():
                if token.targets(tag) or token == tag:
                    current_tag_group.remove(tag)
                    applied = True

            if not applied:
                continue

        current_tag_group.append(token)

    yield from _diff_previous()


def tokens_to_markup(tokens: list[Token]) -> str:
    """Converts a token stream into the markup of its tokens.

    Args:
        tokens: Any list of Token objects. Usually obtained from `tokenize_markup` or
            `tokenize_ansi`.

    Returns:
        The markup the given tokens represent.
    """

    tags: list[Token] = []
    markup = ""

    for token in tokens:
        if token.is_plain():
            if len(tags) > 0:
                markup += f"[{' '.join(tag.markup for tag in tags)}]"

            markup += token.value

            tags = []

        else:
            tags.append(token)

    if len(tags) > 0:
        markup += f"[{' '.join(tag.markup for tag in tags)}]"

    return markup


def get_markup(text: str) -> str:
    """Gets the markup representing an ANSI-coded string."""

    return tokens_to_markup(list(tokenize_ansi(text)))


def optimize_markup(markup: str) -> str:
    """Optimizes markup by tokenizing it, optimizing the tokens and converting it back to markup."""

    return tokens_to_markup(list(optimize_tokens(list(tokenize_markup(markup)))))


PARSERS = {
    PlainToken: parse_plain,
    ColorToken: parse_color,
    StyleToken: parse_style,
    MacroToken: parse_macro,
    AliasToken: parse_alias,
    ClearToken: parse_clear,
    CursorToken: parse_cursor,
}


def _apply_macros(
    text: str, macros: Iterator[tuple[MacroType, tuple[str, ...]]]
) -> str:
    """Applies macros to the given text.

    Args:
        text: The plain text the macros will apply to.
        macros: Any iterator of MacroTokens that will be applied.

    Returns:
        The input plain text, with all macros applied to it. The macros will be applied
        in the order they appear in.
    """

    for method, args in macros:
        if len(args) > 0:
            text = method(*args, text)
            continue

        text = method(text)

    return text


def _sub_aliases(tokens: list[Token], context: ContextDict) -> list[Token]:
    """Substitutes all AliasTokens to their underlying values.

    Args:
        tokens: Any list of Tokens. When this iterator contains nothing
            that can be interpreted as an alias, the same iterator turned into
            a list will be returned.
        context: The context that aliases will be searched in.
    """

    output: list[Token] = []

    # It's more computationally efficient to create this lambda once and reuse it
    # every time. There is no need to define a full function, as it just returns
    # a function return.
    get_full = (
        lambda: tokens_to_markup(  # pylint: disable=unnecessary-lambda-assignment
            tokens
        )
    )

    for token in tokens:
        if token.value in context["aliases"] and (
            Token.is_clear(token) or Token.is_macro(token) or Token.is_alias(token)
        ):
            if Token.is_clear(token) or Token.is_macro(token):
                token = AliasToken(token.value)

            if Token.is_alias(token):
                aliases_parsed = parse_alias(token, context, get_full)
                output.extend(list(tokenize_markup(f"[{aliases_parsed}]")))

            continue

        if Token.is_macro(token) and token.value == "!link":
            warn(
                "Hyperlinks are no longer implemented as macros."
                + " Prefer using the `~{uri}` syntax.",
                DeprecationWarning,
                stacklevel=4,
            )

            output.append(HLinkToken(":".join(token.arguments)))
            continue

        output.append(token)

    return output


# This function could be broken up into pieces, but that will likely lose readability.
def parse_tokens(  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    tokens: list[Token],
    *,
    optimize: bool = False,
    context: ContextDict | None = None,
    append_reset: bool = True,
    ignore_unknown_tags: bool = True,
) -> str:
    """Parses a stream of tokens into the ANSI-coded string they represent.

    Args:
        tokens: Any list of Tokens, usually obtained from either `tokenize_ansi` or
            `tokenize_markup`.
        optimize: If set, `optimize_tokens` will optimize the input iterator before
            usage. This will incur a (minor) performance hit.
        context: The context that aliases and macros found within the tokens will be
            searched in.
        append_reset: If set, `ClearToken("/")` will be appended to the token iterator,
            clearing all styles.
        ignore_unknown_tags: If set, the `MarkupSyntaxError` coming from unknown tags
            will be silenced.

    Returns:
        The ANSI-coded string that the token stream represents.
    """

    if context is None:
        context = create_context_dict()

    token_list = _sub_aliases(tokens, context)

    # It's more computationally efficient to create this lambda once and reuse it
    # every time. There is no need to define a full function, as it just returns
    # a function return.
    get_full = (
        lambda: tokens_to_markup(  # pylint: disable=unnecessary-lambda-assignment
            token_list
        )
    )

    if optimize:
        token_list = list(optimize_tokens(token_list))

    if append_reset:
        token_list.append(ClearToken("/"))

    link = None
    output = ""
    segment = ""
    background = Color.parse("#000000")
    macros: list[MacroToken] = []
    unknown_aliases: list[Token] = []

    save_state: list[Token] = []

    for i, token in enumerate(token_list):
        if token.is_plain():
            value = _apply_macros(
                token.value, (parse_macro(macro, context, get_full) for macro in macros)
            )

            if len(unknown_aliases) > 0:
                output += f"[{' '.join(tkn.value for tkn in unknown_aliases)}]"
                unknown_aliases = []

            output += segment + (
                value if link is None else LINK_TEMPLATE.format(uri=link, label=value)
            )

            segment = ""
            continue

        if token.is_hyperlink():
            link = token.value
            continue

        if Token.is_macro(token):
            macros.append(token)
            continue

        if Token.is_clear(token):
            if token.value in ("/", "/~"):
                link = None

                if token.value == "/~":
                    continue

            found = False
            for macro in macros.copy():
                if token.targets(macro):
                    macros.remove(macro)
                    found = True
                    break

            if found and token.value != "/":
                continue

            if token.value.startswith("/!"):
                raise MarkupSyntaxError(
                    token.value, "has nothing to target", get_full()
                )

        if Token.is_color(token) and token.color.background:
            background = token.color

        if Token.is_pseudo(token):
            if token.value in STATE_PSEUDOS:
                segment += parse_state_pseudo(token, tokens, i, save_state, context)
                continue

            if token.value == "#auto":
                token = ColorToken("#auto", background.contrast)

        try:
            segment += PARSERS[type(token)](token, context, get_full)  # type: ignore

        except MarkupSyntaxError:
            if not ignore_unknown_tags:
                raise

            unknown_aliases.append(token)

    if len(unknown_aliases) > 0:
        output += f"[{' '.join(tkn.value for tkn in unknown_aliases)}]"

    output += segment

    return output


def parse(
    text: str,
    optimize: bool = False,
    context: ContextDict | None = None,
    append_reset: bool = True,
    ignore_unknown_tags: bool = True,
) -> str:
    """Parses markup into the ANSI-coded string it represents.

    Args:
        text: Any valid markup.
        optimize: If set, `optimize_tokens` will optimize the tokens found within the
            input markup before usage. This will incur a (minor) performance hit.
        context: The context that aliases and macros found within the markup will be
            searched in.
        append_reset: If set, `[/]` will be appended to the token iterator, clearing all
            styles.
        ignore_unknown_tags: If set, the `MarkupSyntaxError` coming from unknown tags
            will be silenced.

    Returns:
        The ANSI-coded string that the markup represents.
    """

    if context is None:
        context = create_context_dict()

    if append_reset and not text.endswith("/]"):
        text += "[/]"

    tokens = list(tokenize_markup(text))

    return parse_tokens(
        tokens,
        optimize=optimize,
        context=context,
        append_reset=append_reset,
        ignore_unknown_tags=ignore_unknown_tags,
    )
