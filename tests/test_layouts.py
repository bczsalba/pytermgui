import re

import pytest

import pytermgui as ptg
from pytermgui.window_manager.layouts import Auto, Static


def test_auto():
    layout = ptg.Layout()
    layout.add_slot("Header")
    layout.add_break()
    layout.add_slot("Body")
    layout.add_break()
    layout.add_slot("Footer")

    assert str(layout.header.width) == "Auto(value=0)"

    layout.apply()
    assert len(layout.slots) == 5


def test_static():
    layout = ptg.Layout()
    layout.add_slot("one", width=10, height=15)
    layout.add_break()
    layout.add_slot("two")

    assert str(layout.one.width) == "Static(value=10)"

    layout.apply()

    assert isinstance(layout.one.width, Static)
    assert isinstance(layout.one.height, Static)
    assert isinstance(layout.two.width, Auto)
    assert isinstance(layout.two.height, Auto)


def test_relative():
    layout = ptg.Layout()
    layout.add_slot("one", width=0.9, height=0.1)

    assert (
        re.match(
            r"Relative\(value=[\d]+, scale=0\.9, bound=<function Layout.add_slot.<locals>.<lambda> at 0x[0-9a-fA-F]+>\)",
            str(layout.one.width),
        )
        is not None
    )

    layout.apply()
    assert layout.one.width.value == int(ptg.terminal.width * 0.9)

    with pytest.raises(TypeError):
        layout.one.width.value = 10


def test_detach():
    layout = ptg.Layout()
    slot = layout.add_slot("Body")
    slot.content = ptg.Window()
    layout.apply()

    slot.detach_content()


def test_wrong_detach():
    layout = ptg.Layout()
    slot = layout.add_slot("Body")

    with pytest.raises(AttributeError):
        slot.detach_content()


def test_wrong_getattr():
    layout = ptg.Layout()
    layout.add_slot("Body")

    with pytest.raises(AttributeError):
        layout.body1


def test_add_index():
    layout = ptg.Layout()
    layout.add_slot("Body")
    layout.add_slot("Header", index=0)


def test_assign():
    layout = ptg.Layout()
    layout.add_slot("Body")
    layout.assign(ptg.Container())


def test_wrong_assign():
    layout = ptg.Layout()

    layout.assign(ptg.Container(), index=2)
    assert layout.slots == []
