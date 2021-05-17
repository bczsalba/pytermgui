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
    container += InputField(
        prompt=(
            "you cant edit this.\n"
            + "-------------------\n"
        ),
        value=(
            "this is some\n"
            + "example value\n"
            + "second line\n\n\n\n"
            + "have a nice day!"
        )
    )

    container.forced_height = height

    return container

def field() -> InputField:
    return selected[0]

with alt_buffer(cursor=False):
    InputField.set_class_style("cursor", lambda depth, item: color(item, 72))

    main = Container(vert_align=Container.VERT_ALIGN_TOP)
    splitter = Splitter()

    left = create_container(30)
    splitter += left

    right = create_container(30)
    splitter += right

    main += Container() + splitter
    main.set_char("border", ["|x| ", "=", " |x|", "="])
    main.forced_width = 120

    fields = [left, right]
    selected = left
    field().focus()

    main.center()
    main.print()

    while True:
        key = getch()

        if field().has_selection():
            if key in ["x", keys.BACKSPACE, "d"]:
                field().clear_value()

            field().clear_selected()

        elif key == keys.TAB:
            field().blur()
            selected = fields[len(fields) - 1 - fields.index(selected)]
            field().focus()

        elif key == keys.CTRL_A:
            field().select_range((0, len(field().value) - 1))

        elif key == "*":
            clear()
            print(selected.value.split('\n'))
            getch()

        else:
            field().send(key)

        main.print()
