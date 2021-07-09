#!/usr/bin/env python3
"""
pytermgui/tests/cursor_test.py
------------------------------
author: bczsalba


This file serves to test basic mouse capabilities.
"""

from typing import Optional, Union

from pytermgui import (
    MouseAction,
    ColorPicker,
    InputField,
    Container,
    Splitter,
    ListView,
    Prompt,
    Label,
    getch,
    boxes,
    clear,
    foreground,
    alt_buffer,
    mouse_handler,
    screen_size,
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


with alt_buffer(echo=False, cursor=False), mouse_handler("press_hold") as mouse:
    root = Label("[214 bold]ListView:").get_container()
    root += ListView(["first", "second", "third"])
    root += Label("[214 bold]Prompt:")
    root += Prompt("label", "value")
    root += Label("[214 bold]InputField:")
    root += InputField("hello\nthere")
    root += InputField("obiwan\nkenobi")

    boxes.DOUBLE_TOP.set_chars_of(root)

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

    dragbar = root.define_mouse_target(0, 1, 1, -1)

    for target in cp.mouse_targets:
        target.show(210)
    getch()

    show_targets(root)

    previous_pos: tuple[int, int] = None

    while key := getch():
        mouse_event = mouse(key)

        if mouse_event is None:
            if isinstance(root.selected, InputField):
                root.selected.send(key)

            elif key == "*":
                show_targets(root)
                getch()

        else:
            action, pos = mouse_event

            # Selecting items on press
            if action is MouseAction.PRESS:
                if root.click(pos) is None:
                    root.blur()

            # Moving window around using the top bar
            elif action is MouseAction.HOLD:
                target = root.click(pos)
                if not target is dragbar and previous_pos is None:
                    continue

                if previous_pos is None:
                    previous_pos = pos
                    continue

                # Clearing the whole screen is faster than Container.wipe()
                clear()

                width, height = screen_size()
                new = (
                    min(
                        width - root.width,
                        max(0, root.pos[0] - (previous_pos[0] - pos[0])),
                    ),
                    min(height - root.height, max(0, pos[1])),
                )

                root.pos = new
                previous_pos = pos

            elif action is MouseAction.RELEASE:
                previous_pos = None

        root.print()
