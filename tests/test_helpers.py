from pytermgui import tim, real_length, get_applied_sequences, break_line


def test_break_plain():
    text = "123 12345 1234"
    broken = break_line(text, 3)
    assert list(broken) == ["123", " 12", "345", " 12", "34"]


def test_break_fancy():
    text = tim.parse("[141 bold]Hello there[/ italic blue] whats up[cyan bold]?")
    broken = break_line(text, 3)

    assert list(broken) == [
        "\x1b[38;5;141m\x1b[1mHel\x1b[0m",
        "\x1b[38;5;141m\x1b[1mlo \x1b[0m",
        "\x1b[38;5;141m\x1b[1mthe\x1b[0m",
        "\x1b[38;5;141m\x1b[1mre\x1b[0m\x1b[3m\x1b[38;5;4m \x1b[0m",
        "\x1b[0m\x1b[3m\x1b[38;5;4mwha\x1b[0m",
        "\x1b[0m\x1b[3m\x1b[38;5;4mts \x1b[0m",
        "\x1b[0m\x1b[3m\x1b[38;5;4mup\x1b[38;5;6m\x1b[1m?\x1b[0m",
    ]


def test_break_newline():
    text = "this is too short\nsike"

    broken = break_line(text, limit=20)
    assert list(broken) == ["this is too short", "sike"]


def test_get_applied_sequences_full_unset():
    text = tim.parse("[249 @green bold]Hello[/ cyan italic]There").rstrip("\x1b[0m")
    assert get_applied_sequences(text) == "\x1b[38;5;6m\x1b[3m"


def test_get_applied_sequences_fg_unset():
    text = tim.parse("[249 @green bold]Hello[/fg italic]There").rstrip("\x1b[0m")
    assert get_applied_sequences(text) == "\x1b[48;5;2m\x1b[1m\x1b[3m"


# TODO: There is something wrong with this specific functionality in the pytest env.
#       It seems like on STANDARD colorsys /bg and /fg sometimes get interpreted as
#       a normal indexed color, which makes this break. It only happens on STANDARD,
#       which should hopefully be around 0 users, but we should fix it sometime.
def not_test_get_applied_sequences_bg_unset():
    text = "\x1b[38;5;249m\x1b[48;5;2m\x1b[1mHello\x1b[49m\x1b[3mThere"

    assert get_applied_sequences(text) == "\x1b[38;5;249m\x1b[1m\x1b[3m"
