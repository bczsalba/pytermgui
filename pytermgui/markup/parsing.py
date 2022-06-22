from __future__ import annotations

from typing import Callable, Iterator, TypedDict
from warnings import filterwarnings, warn

from ..colors import str_to_color
from ..exceptions import ColorSyntaxError
from ..regex import RE_ANSI, RE_MACRO, RE_MARKUP, RE_POSITION
from .tokens import (
    AliasToken,
    ClearToken,
    ColorToken,
    CursorToken,
    HLinkToken,
    MacroToken,
    PlainToken,
    StyleToken,
    Token,
)

# TODO: Improve first-run performance.

filterwarnings("always")

STYLES = {
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

REVERSE_STYLES = {value: key for key, value in STYLES.items()}

CLEARERS = {
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

REVERSE_CLEARERS = {value: key for key, value in CLEARERS.items()}

LINK_TEMPLATE = "\x1b]8;;{uri}\x1b\\{label}\x1b]8;;\x1b\\"


class ContextDict(TypedDict):
    aliases: dict[str, str]
    macros: dict[str, Callable[[str, ...], str]]

    @classmethod
    def create(cls) -> ContextDict:
        return {"aliases": {}, "macros": {}}


def tokenize_markup(text: str) -> Iterator[Token]:
    def _consume(tag: str) -> Token:
        if tag in STYLES:
            return StyleToken(tag)

        if tag.startswith("/"):
            return ClearToken(tag)

        if tag.startswith("!"):
            matchobj = RE_MACRO.match(tag)

            if matchobj is not None:
                name, args = matchobj.groups()

                if args is None:
                    return MacroToken(name, [])

                return MacroToken(name, args.split(":"))

        if tag.startswith("~"):
            return HLinkToken(tag[1:])

        if tag.startswith("(") and tag.endswith(")"):
            values = tag[1:-1].split(";")
            if len(values) != 2:
                raise ValueError(
                    f"Cursor tags must have exactly 2 values delimited by `;`, got {tag!r}."
                )

            return CursorToken(tag[1:-1], *map(int, values))

        token: Token
        try:
            token = ColorToken(tag, str_to_color(tag))

        except ColorSyntaxError:
            token = AliasToken(tag)

        finally:
            return token  # pylint: disable=lost-exception

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

            consumed = _consume(tag)
            if has_inverse:
                if consumed.markup == "/fg":
                    consumed = ClearToken("/fg")

                elif consumed.markup == "/bg":
                    consumed = ClearToken("/bg")

            yield consumed

        cursor = end

    if cursor < length:
        yield PlainToken(text[cursor:length])


def tokenize_ansi(text: str) -> list[Token]:
    def _is_256(code: str) -> bool:
        return code.startswith("38;5;") or code.startswith("48;5;")

    def _is_rgb(code: str) -> bool:
        return code.startswith("38;2;") or code.startswith("48;2;")

    def _is_std(code: str) -> bool:
        return code.isdigit() and (30 <= int(code) <= 47 or 90 <= int(code) <= 107)

    cursor = 0
    for matchobj in RE_ANSI.finditer(text):
        full, content, *_ = matchobj.groups()

        start, end = matchobj.span()

        if cursor < start:
            yield PlainToken(text[cursor:start])

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

            yield CursorToken(content, ypos or None, xpos or None)
            continue

        # TODO: Links could also be parsed, though not sure how useful that would be.

        stylestream: list[Token] = []

        for part in reversed(content.split(";")):
            code = part + (";" if code != "" else "") + code

            # Style
            if code in REVERSE_STYLES:
                stylestream.append(StyleToken(REVERSE_STYLES[code]))
                code = ""
                continue

            if code in REVERSE_CLEARERS:
                stylestream.append(ClearToken(REVERSE_CLEARERS[code]))
                code = ""
                continue

            if not _is_256(code) and not _is_rgb(code) and not _is_std(code):
                continue

            # Color
            try:
                color = str_to_color(code)
                code = ""
                stylestream.append(ColorToken(code, color))

            except ColorSyntaxError as error:
                raise ValueError(f"Cannot parse {code!r}.") from error

        yield from reversed(stylestream)

    remaining = text[cursor:]
    if len(remaining) > 0:
        yield PlainToken(remaining)


def eval_alias(text: str, context: ContextDict) -> str:
    aliases = context["aliases"]

    evaluated = ""
    for tag in text.split():
        if tag not in aliases:
            evaluated += tag + " "
            continue

        evaluated += eval_alias(aliases[tag], context)

    return evaluated.rstrip(" ")


def parse_plain(token: PlainToken, _: ContextDict) -> str:
    return token.value


def parse_color(token: ColorToken, _: ContextDict) -> str:
    return token.color.sequence


def parse_style(token: StyleToken, _: ContextDict) -> str:
    index = STYLES[token.value]

    return f"\x1b[{index}m"


def parse_macro(
    token: MacroToken, context: ContextDict
) -> tuple[Callable[[str, ...], str], tuple[str, ...]]:
    func = context["macros"].get(token.value)

    if func is None:
        raise ValueError(f"Undefined macro {token.value!r}.")

    return func, token.arguments


def parse_alias(token: AliasToken, context: ContextDict) -> str:
    if token.value not in context["aliases"]:
        return token.value

    meaning = context["aliases"][token.value]

    return eval_alias(meaning, context).rstrip(" ")


def parse_clear(token: ClearToken, _: ContextDict) -> str:
    index = CLEARERS[token.value]

    return f"\x1b[{index}m"


def parse_cursor(token: CursorToken, _: ContextDict) -> str:
    ypos, xpos = map(lambda i: "" if i is None else i, token)

    return f"\x1b[{ypos};{xpos}H"


def optimize_tokens(tokens: Iterator[Token]) -> Iterator[Token]:
    previous = []
    current_tag_group = []

    def _diff_previous() -> Iterator[Token]:
        applied = previous.copy()

        for tkn in current_tag_group:
            targets = []

            if tkn.is_clear():
                targets = [tkn.targets(tag) for tag in applied]

            if tkn in previous and not tkn.is_clear():
                continue

            if tkn.is_clear() and not any(targets):
                continue

            applied.append(tkn)
            yield tkn

    def _remove_redundant_color(token: Token) -> None:
        for applied in current_tag_group.copy():
            if applied.is_clear() and applied.targets(token):
                current_tag_group.remove(applied)

            if not applied.is_color():
                continue

            old = applied.color

            if old.background == new.background:
                current_tag_group.remove(applied)

    for token in tokens:
        if token.is_plain():
            yield from _diff_previous()
            yield token

            previous = current_tag_group.copy()

            continue

        if token.is_color():
            new = token.color

            _remove_redundant_color(token)

            if not any(token.markup == applied.markup for applied in current_tag_group):
                current_tag_group.append(token)

            continue

        if token.is_style():
            if not any(token == tag for tag in current_tag_group):
                current_tag_group.append(token)

            continue

        if token.is_clear():
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
    tags = []
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


def optimize_markup(markup: str) -> str:
    return tokens_to_markup(optimize_tokens(tokenize_markup(markup)))


PARSERS = {
    PlainToken: parse_plain,
    ColorToken: parse_color,
    StyleToken: parse_style,
    MacroToken: parse_macro,
    AliasToken: parse_alias,
    ClearToken: parse_clear,
    CursorToken: parse_cursor,
}


def _apply_macros(text: str, macros: Iterator[MacroToken]) -> str:
    """Apply current macros to text"""

    for method, args in macros:
        if len(args) > 0:
            text = method(*args, text)
            continue

        text = method(text)

    return text


def _sub_aliases(text: str, context: ContextDict) -> str:
    line = ""
    tags = []

    for token in tokenize_markup(text):
        if token.is_plain():
            if len(tags) > 0:
                line += f"[{' '.join(tags)}]"

            value = token.value

            # TODO: This isn't great.
            #       - Things that _wouldn't be parsed (like `times[i]`) are ignored and thus
            #         their brackets are removed in the parsed output
            #       - Some macros (like !gradient) seem to re-escape text for some reason.
            #
            #       Honestly, this might be a full non-issue, and it might just be better to
            #       immediately parse things like highlight results, and not use macros between.
            if RE_MARKUP.match(value) is not None:
                value = value.replace("[", r"\[")

            line += value

            tags = []
            continue

        if token.is_alias() or token.is_macro() and token.value in context["aliases"]:
            tags.append(parse_alias(token, context))

            continue

        if token.is_clear() and token.value in context["aliases"]:
            tags.append(parse_alias(AliasToken(token.value), context))
            continue

        if token.is_macro() and token.value == "!link":
            warn(
                "Hyperlinks are no longer implemented as macros."
                + " Prefer using the `~{uri}` syntax.",
                DeprecationWarning,
                stacklevel=4,
            )
            token = HLinkToken(":".join(token.arguments))

        tags.append(token.markup)

    if len(tags) > 0:
        line += f"[{' '.join(tags)}]"

    return line


def parse(
    text: str,
    optimize: bool = False,
    context: ContextDict | None = None,
    append_reset: bool = True,
) -> str:
    if context is None:
        context = ContextDict.create()

    text = _sub_aliases(text, context)

    if append_reset and not text.endswith("/]"):
        text += "[/]"

    output = ""
    segment = ""
    macros = []
    link = None

    tokens: Iterator[Token] = tokenize_markup(text)
    if optimize:
        tokens = optimize_tokens(tokens)

    for token in tokens:
        if token.is_plain():
            part = segment + _apply_macros(
                token.value, (parse_macro(macro, context) for macro in macros)
            )

            output += (
                part if link is None else LINK_TEMPLATE.format(uri=link, label=part)
            )

            segment = ""
            continue

        if token.is_hyperlink():
            link = token.value
            continue

        if token.is_macro():
            macros.append(token)
            continue

        if token.is_clear():
            if token.value == "/~":
                link = None
                continue

            found = False
            for macro in macros.copy():
                if token.targets(macro):
                    macros.remove(macro)
                    found = True
                    break

            if found:
                continue

            if token.value.startswith("/!"):
                raise ValueError(
                    f"Cannot use clearer {token.value!r} with nothing to target."
                )

        segment += PARSERS[type(token)](token, context)

    output += segment

    return output
