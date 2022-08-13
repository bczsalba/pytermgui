from pytermgui import highlight_python


def test_literal_highlight():
    assert (
        highlight_python("'[This is a test]'")
        == r"[code.str]'[This is a test]'[/code.str]"
    )
