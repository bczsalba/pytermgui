"""
pytermgui/tests/container_test.py
--------------------------------
author: bczsalba


This is a really simple file to test basic Container and other element
actions, will probably be removed once those are reliable.
"""

from pytermgui import Container, Label, alt_buffer, getch

with alt_buffer():
    c = Container()
    c.chars["border"] = ["|x| ", "=", " |x|", "="]

    c += Label("hello world!")

    d = Container()
    d += Label("hello inner scope!")

    e = Container()
    e += Label("hello inner-er scope!")

    f = Container()
    f += Label("this is getting ridiculous")

    e += f
    d += e
    c += d

    c.pos = (35, 10)
    print(c)
    getch()
