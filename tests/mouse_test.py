#!/usr/bin/env python3
"""
pytermgui/tests/cursor_test.py
------------------------------
author: bczsalba


This file serves to test basic mouse capabilities.
"""

from typing import Optional, Union

from pytermgui import alt_buffer, report_mouse, getch, clear, print_to
from pytermgui import foreground256 as color


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

    pos = (0, 0)
    while key := getch():
        clear()
        pos, pressed = parse_mouse(key)

        if pos is None:
            print_to((0, 0), "key: " + key)

        elif pos is ValueError:
            continue

        else:
            print_to(pos, color(("." if pressed else "x"), 210))

report_mouse("movement", action="stop")
