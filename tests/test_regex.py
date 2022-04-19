import pytermgui as ptg
from pytermgui.regex import strip_ansi, strip_markup, real_length, has_open_sequence


def test_strip_ansi():
    assert strip_ansi(ptg.tim.parse("[141 @61]This is a test")) == "This is a test"


def test_real_length():
    assert real_length(ptg.tim.parse("[!rainbow]Test string")) == len("Test string")


def test_strip_markup():
    assert strip_markup("[141 @61 !upper]This is a test") == "This is a test"


def test_has_open_sequence():
    assert not has_open_sequence(ptg.tim.parse("[141]Hello!"))

    assert has_open_sequence("\x1b[1")
    assert not has_open_sequence("\x1b[1m")
    assert not has_open_sequence("\x1b[1mHello")

    assert has_open_sequence("\x1b]")
    assert not has_open_sequence("\x1b]1\x1b\\")
    assert not has_open_sequence("\x1b]30;2ST\x1b\\Hello")

    assert has_open_sequence("\x1b_G")
    assert has_open_sequence("\x1b_GthisstringcanHaveanycharacters")
    assert not has_open_sequence("\x1b_GthisstringcanHaveanycharacters\x1b\\")

    assert has_open_sequence("\x1b[Something\x1b\\")
    assert has_open_sequence("\x1b]SomethingmH")
    assert has_open_sequence("\x1b_GSomethingmH")

    assert not has_open_sequence(
        ptg.tim.parse("[141]Hello[/fg bold italic]There[@61 inverse]Text")
    )

    assert has_open_sequence("\x1b[38;5;141hello I aM Missing a lowercase M\x1b[1m")
