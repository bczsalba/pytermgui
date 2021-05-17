"""
pytermgui/tests/inputfield_test.py
-----------------------------------
author: bczsalba


This file creates a double-split interface with two different inputfields.
"""

from typing import Callable
from pytermgui import (
    Container,
    Splitter,
    InputField,
    alt_buffer,
    getch,
    keys,
    clear,
    background256 as color,
)

def create_container(height: int = 0):
    """Create container with the same data"""

    container = Container(vert_align=Container.VERT_ALIGN_TOP)
    container.set_char("border", ["│ ", "─", " │", "─"])
    container.set_char("corner", ["╭", "╮", "╯", "╰"])
    container += InputField("this is some\nexample value\nsecond line\nthird line\nhave a nice day!")
    container.forced_height = height

    return container


with alt_buffer(cursor=True):
    main = Container(vert_align=Container.VERT_ALIGN_TOP)
    splitter = Splitter()

    left = create_container(35)
    splitter += left

    right = create_container(35)
    splitter += right

    main += Container() + splitter
    main.forced_width = 149

    main.set_char("border", ["|x| ", "=", " |x|", "="])

    main.center()
    main.print()

    fields = [left[0], right[0]]
    selected = left[0]
    while True:
        key = getch()

        if key == keys.TAB:
            selected = fields[len(fields) - 1 - fields.index(selected)]
        if key == "*":
            clear()
            print(selected.value.split('\n'))
            getch()
        else:
            selected.send(key)

        main.print()
