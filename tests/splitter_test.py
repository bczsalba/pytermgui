"""
pytermgui/tests/splitter_test.py
--------------------------------
author: bczsalba


This test file shows the basic functionality that Splitter-s provide.
"""

from pytermgui import (
    Container,
    Prompt,
    Label,
    Splitter,
    alt_buffer,
    getch,
    ListView,
    ColorPicker,
    real_length,
)

with alt_buffer(cursor=False):
    Container.set_char("border", ["│ ", "─", " │", "─"])
    Container.set_char("corner", ["╭", "╮", "╯", "╰"])
    Splitter.set_char("separator", " ")

    main = Container(horiz_align=Container.HORIZ_ALIGN_LEFT)

    header = Splitter()
    header += Label("color picker one:", Label.ALIGN_LEFT)
    # header += Label("one", Label.ALIGN_CENTER)
    # header += Label("onne", Label.ALIGN_CENTER)
    # header += Label("onne", Label.ALIGN_CENTER)
    header += Label("color picker two:", Label.ALIGN_RIGHT)

    splitter = Splitter()
    splitter += ColorPicker(16)
    splitter += ColorPicker(16)

    main += header
    main += splitter

    main += ColorPicker(20)
    main += Label("color picker three:")

    main.center()
    main.print()

    while getch():
        pass
