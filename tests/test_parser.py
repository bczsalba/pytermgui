from __future__ import annotations

import random
import string
from itertools import zip_longest

import pytest

from pytermgui import (
    StyledText,
    pretty,
    tim,
    tokenize_ansi,
    tokens_to_markup,
    tokenize_markup,
)
from pytermgui.colors import Color, str_to_color
from pytermgui.markup import StyledText, Token
from pytermgui.markup import tokens as tkns
from pytermgui.markup.parsing import parse_tokens
from pytermgui.markup.style_maps import CLEARERS, STYLES


def random_plain() -> tkns.PlainToken:
    value = "".join(random.choices(string.ascii_letters, k=5))
    value = (
        value.replace("\n", " ")
        .replace("\r", " ")
        .replace("\x0b", " ")
        .replace("\x0c", " ")
    )

    return tkns.PlainToken(value[: random.randint(1, len(value) - 1)])


def random_color() -> tkns.ColorToken:
    background = random.randint(0, 1)

    def _random_std() -> Color:
        value = str(random.randint(0, 15))

        if background:
            value = "@" + value

        return value, str_to_color(value)

    def _random_256() -> Color:
        value = str(random.randint(0, 255))

        if background:
            value = "@" + value

        return value, str_to_color(value)

    def _random_rgb() -> Color:
        value = ";".join(map(str, (random.randint(0, 256) for _ in range(3))))

        if background:
            value = "@" + value

        return value, str_to_color(value)

    generators = [_random_std, _random_256, _random_rgb]

    generate = random.choice(generators)
    return tkns.ColorToken(*generate())


def random_style() -> tkns.StyleToken:
    return tkns.StyleToken(random.choice(list(STYLES.keys())))


def random_clear() -> tkns.ClearToken:
    return tkns.ClearToken(random.choice(list(CLEARERS.keys())))


def random_cursor() -> tkns.CursorToken:
    pos = tuple(map(str, (random.randint(0, 24), random.randint(0, 80))))
    return tkns.CursorToken(f"{pos[0]};{pos[1]}", pos[0], pos[1])


def random_hlink() -> tkns.HLinkToken:
    return tkns.HLinkToken("".join(random.choices(string.ascii_letters, k=20)))


class TestParser:
    def test_length(self):
        output = StyledText.first_of(tim.parse("[141 @61 bold]One"))
        print(output)

        assert len(output) == len(output.plain) == len("One")

    def test_styledtext_index(self):
        text = StyledText.first_of(tim.parse("[141 @61 bold]Test"))
        assert text[1] == "\x1b[38;5;141m\x1b[48;5;61m\x1b[1me", ascii(text[1])

    def test_sequence_redundancy(self):
        output = tim.parse(
            "[123 245 bold /bold italic]Test", append_reset=False, optimize=True
        )
        assert output == "\x1b[38;5;245m\x1b[3mTest", repr(output)

    def test_get_markup(self):
        base = "[141 @61 bold]Hello[/]"
        ansi = tim.parse("[141 @61 bold]Hello")
        markup = tim.get_markup(ansi)
        assert base == markup

    def test_mutiline_markup(self):
        base = "[141 @61 bold]Hello[/]\nWhat a beautifull day to look a this [~https://example.com]website[/~] !\nOh and this [~https://example.com]website also[/~]\nHave a nice day !"
        opti_base = "[141 @61 bold]Hello[/]\nWhat a beautifull day to look a this [~https://example.com]website[/~] !\nOh and this [~https://example.com]website also[/~]\nHave a nice day ![/]"

        tokens = tokenize_markup(base)
        ansi = parse_tokens(list(tokens))
        tokens2 = tokenize_ansi(ansi)
        markup = tokens_to_markup(list(tokens2))
        assert opti_base == markup

        ansi = tim.parse(base)
        markup = tim.get_markup(ansi)
        assert opti_base == markup

    def test_parse(self):
        assert (
            tim.parse("[141 @61 bold !upper]Hello")
            == "\x1b[38;5;141m\x1b[48;5;61m\x1b[1mHELLO\x1b[0m"
        ), repr(tim.parse("[141 @61 bold !upper]Hello"))


class TestFunctionality:
    def test_alias(self):
        tim.alias("test", "141")
        assert tim.parse("[test]Test") == tim.parse("[141]Test")

    def test_define(self):
        tim.define("!upper", lambda item: item.upper())
        assert tim.parse("[!upper]test", append_reset=False) == "TEST"
        assert tim.parse("[!upper 141]test") == tim.parse("[141]TEST")

    def test_pprint_works(self):
        for obj in [{1, 2, 3}, "test", set, list(range(10)), {"abc": "efg"}]:
            pretty.pprint(obj)

    def test_displayhook_works(self):
        pretty.install()


def test_random_tokens() -> None:
    def _get_next(previous: tkns.Token | None) -> tkns.Token:
        generators = [
            random_plain,
            random_color,
            random_style,
            random_clear,
        ]

        if previous is not None and (previous.is_plain() or previous.is_hyperlink()):
            generators.remove(random_plain)

        return random.choice(generators)()

    tokens = []
    previous = None
    for _ in range(50):
        previous = _get_next(previous)
        tokens.append(previous)

    markup = tokens_to_markup(tokens)
    ansi = tim.parse(markup, append_reset=False)

    reverse = list(tokenize_ansi(ansi))

    for expected, real in zip_longest(tokens, reverse, fillvalue=None):
        if expected != real:
            print(expected, real, sep=" != ")

        assert expected == real, f"Expected {expected}, got {real}"

    assert tokens == reverse
