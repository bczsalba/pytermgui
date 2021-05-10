"""
pytermgui/tests/container_test.py
--------------------------------
author: bczsalba


This is a really simple file to test basic Container and other element
actions, will probably be removed once those are reliable.
"""

from pytermgui import Container, Label, alt_buffer, getch, report_mouse
from pytermgui import foreground256 as color

def style(depth: int, item: str) -> str:
    """Test style"""

    return color(item, 213 - depth * 36)

with alt_buffer(cursor=False):
    c = Container()
    c.set_char("border", ["|x| ", "=", " |x|", "="])

    l = Label("hello world!")
    l.set_style("value", style)
    c += l

    d = Container()
    l = Label("hello inner scope!")
    d.set_char("border", ["|| ", "-", " ||", "-"])
    l.set_style("value", style)
    d += l 

    e = Container()
    l = Label("hello inner-er scope!")
    l.set_style("value", style)
    e += l 

    f = Container()
    l = Label("this is getting ridiculous")
    l.set_style("value", style)
    f += l 

    e += f
    d += e
    c += d

    c.pos = (35, 10)
    print(c)
    getch()
