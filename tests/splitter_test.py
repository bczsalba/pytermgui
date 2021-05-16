"""
pytermgui/tests/splitter_test.py
--------------------------------
author: bczsalba


This test file shows the basic functionality that Splitter-s provide.
"""

from pytermgui import Container, Prompt, Label, Splitter, alt_buffer, getch, ListView, ColorPicker, real_length

with alt_buffer(cursor=False):
    Container.set_class_char("border", ["│ ", "─", " │", "─"])
    Container.set_class_char("corner", ["╭", "╮", "╯", "╰"])
    Splitter.set_class_char("separator", " ")
    
    main = Container()

    header = Splitter()
    header += Label("color picker one:", Label.ALIGN_LEFT)
    header += Label("color picker two:", Label.ALIGN_RIGHT)

    splitter = Splitter()
    splitter += ColorPicker(12)
    splitter += ColorPicker(12)

    main += header
    main += splitter

    main += ColorPicker(25)
    main += Label("color picker three:")

    main.center()
    main.print()

    while getch():
        pass
