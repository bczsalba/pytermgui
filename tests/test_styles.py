import pytest

import pytermgui as ptg


class TestStyles:
    @pytest.fixture(autouse=True)
    def _setup(self):
        ptg.Container.styles.border = "60"

        self.container = ptg.Container()
        self.window = ptg.Window()

        self.target_formatter = ptg.StyleCall(
            self.container, ptg.MarkupFormatter("[60]{item}")
        )

    def test_style_branches(self):
        assert ptg.Container.styles.border != ptg.Window.styles.border

        ptg.Container.styles.border = "153"
        assert ptg.Container.styles.border != ptg.Window.styles.border

        self.window.styles.border = "153"
        assert self.container.styles.border.method != self.window.styles.border.method

    def test_style_key_error(self):
        with pytest.raises(KeyError):
            self.container.styles.this_does_not_exist = "Hello"

    def test_style_expansion(self):
        def _assert_equals(short: str, long: str) -> bool:
            assert ptg.StyleManager.expand_shorthand(short).markup == long

        _assert_equals("60", "[60]{item}")
        _assert_equals("141 bold", "[141 bold]{item}")
        _assert_equals("", "{item}")
        _assert_equals("[!rainbow]Test {item}{depth}", "[!rainbow]Test {item}{depth}")

    def test_old_api(self):
        self.container.set_style("border", "60")
        assert self.container._get_style("border") == self.target_formatter

        self.container.set_style("border", self.target_formatter)
        assert self.container._get_style("border") == self.target_formatter

        assert self.container.styles.border == self.container._get_style("border")

    def test_multiple_styles(self):
        self.container.styles.border__corner = "60"

        assert (
            self.container.styles.border
            == self.container.styles.corner
            == self.target_formatter
        )
