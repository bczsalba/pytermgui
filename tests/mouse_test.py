#!/usr/bin/env python3
"""
pytermgui/tests/cursor_test.py
------------------------------
author: bczsalba


This file serves to test basic mouse capabilities.
"""

from typing import Optional, Union

from pytermgui import (
    alt_buffer,
    mouse_handler,
    getch,
    foreground,
    ListView,
    Prompt,
    InputField,
    Splitter,
    Label,
    Container,
    ColorPicker,
    boxes,
)


def show_targets(root: Container) -> None:
    """Debug all root mouse targets"""

    for widget in root:
        for target in widget.mouse_targets:
            target.show(103)

    for target in root.mouse_targets:
        target.show(103)


def set_value(button: ListView, value: str) -> None:
    """Set widget value"""

    button.options = [value]


with alt_buffer(echo=False, cursor=False), mouse_handler("press") as mouse:
    boxes.DOUBLE.set_chars_of(Container)

    root = Label("[214 bold]ListView:").get_container()
    root += ListView(["first", "second", "third"])
    root += Label("[214 bold]Prompt:")
    root += Prompt("label", "value")
    root += Label("[214 bold]InputField:")
    root += InputField("hello\nthere")
    root += InputField("obiwan\nkenobi")

    cp = ColorPicker(16)
    cp += ListView(["hello"])
    cp[-1].onclick = lambda target, widget: print("this shouldn't work!")

    button = ListView(["background"])
    button.onclick = lambda target, widget: (
        cp.toggle_layer(),
        set_value(widget, ("foreground" if cp.layer == 0 else "background")),
    )

    root += cp
    root += button

    root.forced_width = 100
    root.center().print()

    cp.print()
    for target in cp.mouse_targets:
        target.show(210)
    getch()

    show_targets(root)

    while key := getch():
        mouse_event = mouse(key)

        if mouse_event is None:
            if isinstance(root.selected, InputField):
                root.selected.send(key)

            elif key == "*":
                show_targets(root)
                getch()

        else:
            pressed, pos = mouse_event

            if pressed:
                if root.click(pos) is None:
                    root.blur()

        root.print()
