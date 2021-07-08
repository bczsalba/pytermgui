#!/usr/bin/env python3
"""
pytermgui/tests/cursor_test.py
------------------------------
author: bczsalba


This file serves to test basic mouse capabilities.
"""

from typing import Optional, Union

from pytermgui import alt_buffer, report_mouse, translate_mouse, getch, foreground, ListView, Prompt, InputField, Label


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


with alt_buffer(echo=False, cursor=False):
    report_mouse("press")

    root = Label("[214 bold]ListView:").get_container()
    root += ListView(["first", "second", "third"])
    root += Label("[214 bold]Prompt:")
    root += Prompt("label", "value")
    root += Label("[214 bold]InputField:")
    root += InputField("hello\nthere")

    root.forced_width = 50
    root.center().print()
    for widget in root:
        for t in widget.mouse_targets: 
            t.debug(103)

    while key := getch():
        translated = translate_mouse(key)

        if translated is None:
            continue

        pressed, pos = translated
        if pressed:
            root.blur()
            if not root.click(pos):
                root.blur()

        root.print()
        # for t in root[0].mouse_targets: t.debug('124')

report_mouse("movement", action="stop")
