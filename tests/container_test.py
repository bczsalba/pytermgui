"""
pytermgui/tests/container_test.py
--------------------------------
author: bczsalba


This is a really messy file to test basic Container and other element
actions, will probably be removed once those are reliable.
"""

from pytermgui import Container, Label, ListView, Prompt, alt_buffer, getch, report_mouse
from pytermgui import foreground256 as color
from pytermgui import background256 as bg
from typing import Callable

def style(depth: int, item: str) -> str:
    """Test style"""

    return color(item, 213 - depth * 36)

def background(depth: int, item: str) -> str:
    return bg(item, 60)

def colored(pre_color: int) -> Callable[[int, str], str]:
    """Return a lambda with color stuff"""

    return lambda depth, item: color(item, pre_color)

with alt_buffer(cursor=False):
    Container.set_class_char("border", ["|x| ", "=", " |x|", "="])
    
    Label.set_class_style("value", style)
    Prompt.set_class_style("value", style)
    Prompt.set_class_style("delimiter", colored(210))
    Prompt.set_class_style("value", colored(72))
    Prompt.set_class_style("highlight", lambda depth, item: bg(item, 22))
    ListView.set_class_style("delimiter", colored(210))
    ListView.set_class_style("value", colored(72))
    ListView.set_class_style("highlight", lambda depth, item: bg(item, 22))

    c = Container(vert_align=Container.VERT_ALIGN_CENTER, horiz_align=Container.HORIZ_ALIGN_RIGHT)
    c.forced_width = 70

    c += Label("Please excuse how terrible this looks")
    c += Label()
    l = Label("hello world!")
    c += l

    d = Container(vert_align=Container.VERT_ALIGN_BOTTOM)
    l = Label("hello inner scope!")
    d.forced_width = 50
    d.forced_height = 15
    d += l 

    e = Container()
    l = Label("hello inner-er scope!")
    e += l 

    f = Container()
    l = Label("this is getting ridiculous")
    f += l 

    e += f
    d += e
    c += d

    p = Prompt("hello", "there", 2)
    c += p

    lv = ListView(options=["hello", "tehre", "master", "kenobi"], align=Label.ALIGN_CENTER, padding=0)
    c += lv

    c.get_lines()
    c.select(0)
    c.center()

    while True:
        key = getch()

        if key == "k":
            c.selected_index -= 1
        elif key == "j":
            c.selected_index += 1

        c.select()
        c.print()
