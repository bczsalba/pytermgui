#!/usr/bin/env python3
"""
pytermgui/tests/cursor_test.py
------------------------------
author: bczsalba


This file serves to test basic mouse capabilities.
"""

from typing import Optional, Union

from pytermgui import alt_buffer, mouse_handler, getch, foreground, ListView, Prompt, InputField, Splitter, Label, Container


def parse_mouse(code: str) -> Optional[Union[tuple[tuple[int], bool], Exception]]:
    """Parse mouse codes"""

    if not len(code) > 2 or not code[2] == "<":
        return None, None

    nums = code.split(";")[1:]
    is_pressed = nums[1][-1] == "M"
    nums[1] = nums[1][:-1]

    try:
        ints = [int(num) for num in nums]
    except ValueError:
        # this gets triggered when the parameter for `code` is
        # not valid
        return ValueError, False

    ints[0] -= 1

    return tuple(ints), is_pressed

def show_targets(root: Container) -> None:
    """Debug all root mouse targets"""

    for widget in root:
        for target in widget.mouse_targets: 
            target.show(103)

with alt_buffer(echo=False, cursor=False), mouse_handler("press") as mouse:
    root = Label("[214 bold]ListView:").get_container()
    root += ListView(["first", "second", "third"])
    root += Label("[214 bold]Prompt:")
    root += Prompt("label", "value")
    root += Label("[214 bold]InputField:")
    root += InputField("hello\nthere")
    root += InputField("obiwan\nkenobi")

    root.forced_width = 100
    root.center().print()

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
                # root.blur()

                if not root.click(pos):
                    root.blur()

        root.print()
