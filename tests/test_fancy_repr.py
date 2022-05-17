from pytermgui.fancy_repr import FancyYield, build_fancy_repr


class SupportsFancyRepr:
    def __fancy_repr__(self) -> str:
        yield f"<{type(self).__name__} test: 123, no_highlight: "
        yield {"text": "CapitalLetters", "highlight": False}
        yield {"text": " always_highlight()", "highlight": True}
        yield ">"


def test_fancy_repr():
    assert build_fancy_repr(SupportsFancyRepr()) == (
        "<[code.global]SupportsFancyRepr[/code.global]"
        + " test: [code.number]123[/code.number], no_highlight: CapitalLetters"
        + " [code.identifier]always_highlight[/code.identifier]()>"
    )
