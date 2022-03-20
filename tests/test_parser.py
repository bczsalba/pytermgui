from pytermgui import tim, StyledText, pretty
from pytermgui.parser import Token, TokenType, STYLE_MAP, StyledText
from pytermgui.colors import str_to_color


class TestParser:
    def test_return_type(self):
        assert isinstance(tim.parse(""), StyledText)

    def test_length(self):
        output = tim.parse("[141 @61 bold]One[inverse /bold]Other")

        assert len(output) == len(output.plain) == len("OneOther")

    def test_styledtext_index(self):
        text = tim.parse("[141 @61 bold]Test")
        assert text[1] == "e", ascii(text[1])

    def test_sequence_redundancy(self):
        output = tim.parse("[123 245]Test[yellow]")
        assert output == tim.parse("[245]Test"), tim.prettify(output)

    def test_get_markup(self):
        base = "[141 @61 bold]Hello"
        ansi = tim.parse("[141 @61 bold]Hello")
        markup = tim.get_markup(ansi)
        assert base == markup

    def test_parse(self):
        assert (
            tim.parse("[141 @61 bold !upper]Hello")
            == "\x1b[38;5;141m\x1b[48;5;61m\x1b[1mHELLO\x1b[0m"
        )

    def test_pretty_markup(self):
        markup = "[141 bold]Hello[/bold /fg dim italic]There[/]"
        assert StyledText(tim.prettify_markup(markup)).plain == markup


class TestFunctionality:
    def test_alias(self):
        tim.alias("test", "141")
        assert tim.parse("[test]Test") == tim.parse("[141]Test")

    def test_define(self):
        tim.define("!upper", lambda item: item.upper())
        assert tim.parse("[!upper]test") == "TEST"
        assert tim.parse("[!upper 141]test") == tim.parse("[141]TEST")

    def test_pprint_works(self):
        for obj in [{1, 2, 3}, "test", set, list(range(10)), {"abc": "efg"}]:
            pretty.pprint(obj)

    def test_displayhook_works(self):
        pretty.install()


class TestTokens:
    def test_plain(self):
        token = Token(ttype=TokenType.PLAIN, data="Plain")
        assert token.name == "Plain"
        assert token.sequence is None

    def test_style(self):
        for name, index in STYLE_MAP.items():
            token = Token(ttype=TokenType.STYLE, data=index)
            assert token.name == index
            assert token.sequence == f"\x1b[{index}m"

    def test_macro(self):
        token = list(tim.tokenize_markup("[!gradient(60)]Test"))[0]
        assert token.name == "!gradient(60)"
        assert token.ttype is TokenType.MACRO
        assert token.data == (tim.macros["!gradient"], ["60"])

    def test_unsetter(self):
        token = list(tim.tokenize_markup(r"\[bold]Test"))[0]
        assert token.name == token.data == "[bold]"
        assert token.ttype is TokenType.ESCAPED

    def test_fg_8bit(self):
        token = Token(ttype=TokenType.COLOR, data=str_to_color("141"))
        assert token.sequence == "\x1b[38;5;141m"

    def test_bg_8bit(self):
        token = Token(ttype=TokenType.COLOR, data=str_to_color("@141"))
        assert token.sequence == "\x1b[48;5;141m"

    def test_fg_rgb(self):
        token = Token(ttype=TokenType.COLOR, data=str_to_color("000;111;222"))
        assert token.sequence == "\x1b[38;2;0;111;222m"

    def test_bg_rgb(self):
        token = Token(ttype=TokenType.COLOR, data=str_to_color("@123;61;231"))
        assert token.sequence == "\x1b[48;2;123;61;231m"

    def test_fg_hex(self):
        token = list(tim.tokenize_markup("[#14C353]Test"))[0]
        assert token.sequence == "\x1b[38;2;20;195;83m"

    def test_bg_hex(self):
        token = list(tim.tokenize_markup("[@#FAC324]Test"))[0]
        assert token.sequence == "\x1b[48;2;250;195;36m"

    def test_unsetter(self):
        token = Token(ttype=TokenType.UNSETTER, name="/inverse", data="27")
        assert token.sequence == "\x1b[27m"
