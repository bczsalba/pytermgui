"""
pytermgui/tests/container_test.py
--------------------------------
author: bczsalba


This is a really messy file to test basic Container and other widget
actions, will probably be removed once those are reliable.
"""

from typing import Callable
from pytermgui import (
    Container,
    Label,
    ListView,
    Prompt,
    ProgressBar,
    ColorPicker,
    alt_buffer,
    getch,
)

from pytermgui import foreground256 as color
from pytermgui import background256 as highlight


def create_style(pre_color: int) -> Callable[[str], str]:
    """Factory function that creates a callable for color"""

    return lambda depth, item: color(item, pre_color)  # type: ignore


def value_style(depth: int, item: str) -> str:
    """Style function for values"""

    return color(item, 33 + 36 * depth)  # type: ignore


def highlight_style(depth: int, item: str) -> str:
    """Style function for highlighted elements"""

    return highlight(item, 99)


delimiter_style = create_style(225)
padding_label = Label()

with alt_buffer():
    Container.set_class_char("border", ["|| ", "~", " ||", "~"])

    Label.set_class_style("value", value_style)

    Prompt.set_class_style("value", value_style)
    Prompt.set_class_style("label", delimiter_style)
    Prompt.set_class_style("delimiter", delimiter_style)
    Prompt.set_class_style("highlight", highlight_style)

    ListView.set_class_style("highlight", highlight_style)
    ListView.set_class_style("value", value_style)
    ListView.set_class_style("delimiter", delimiter_style)
    ListView.set_class_char("delimiter", ["- ", ""])

    ProgressBar.set_class_style("fill", delimiter_style)
    ProgressBar.set_class_style("delimiter", value_style)

    main = Container()
    main.forced_height = 35
    main.set_char("border", ["|x| ", "=", " |x|", "="])

    main += Label("Please excuse how terrible this looks")
    main += padding_label
    main += Label("hello world!")

    inner = Container() + Label("hello inner scope!")
    inner += Container() + Label("hello inner-er scope!")
    inner[-1] += Container() + Label("this is getting ridonculous.")
    main += inner
    main += padding_label

    main += ColorPicker(36)
    main += padding_label

    main += Prompt("hello", "there")
    main += padding_label
    main += Label("here are some items", Label.ALIGN_LEFT)

    main += ListView(
        ["hello", "tehre", "master", "kenobi"], align=Label.ALIGN_LEFT, padding=2
    )
    progress = 0.0
    main += padding_label
    main += ProgressBar(progress_function=lambda: progress)
    main[-1].forced_width = 100

    main.select(0)
    main.center()
    main.print()

    while True:
        key = getch()

        if key == "k":
            main.selected_index -= 1
        elif key == "j":
            main.selected_index += 1
        elif key == "l":
            progress += 0.01
        elif key == "h":
            progress -= 0.01

        main.select()
        main.print()
