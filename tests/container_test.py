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
    Splitter,
    Label,
    ListView,
    Prompt,
    ProgressBar,
    ColorPicker,
    InputField,
    alt_buffer,
    getch,
    foreground as color,
    background as highlight,
)


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
    Container.set_char("border", ["|| ", "~", " ||", "~"])

    Label.set_style("value", value_style)

    Prompt.set_style("value", value_style)
    Prompt.set_style("label", delimiter_style)
    Prompt.set_style("delimiter", delimiter_style)
    Prompt.set_style("highlight", highlight_style)

    ListView.set_style("highlight", highlight_style)
    ListView.set_style("options", value_style)
    ListView.set_style("delimiter", delimiter_style)

    ProgressBar.set_style("fill", delimiter_style)
    ProgressBar.set_style("delimiter", value_style)

    main = Container(horiz_align=Container.HORIZ_ALIGN_CENTER, vert_align=Container.VERT_ALIGN_CENTER)
    main.forced_height = 37
    main.forced_width = 70
    main.set_char("border", ["|x| ", "=", " |x|", "="])

    main += Label("Please excuse how terrible this looks", markup=False)
    main += padding_label
    main += Label("hello world!", markup=False)

    inner = Container() + Label("hello inner scope!", markup=False)
    inner += Container() + Label("hello inner-er scope!", markup=False)
    inner[-1] += Container() + Label("this is getting ridonculous.", markup=False)
    main += inner
    main += padding_label

    # main += ColorPicker(25)
    # main += padding_label

    main += Prompt("hello", "there")
    main += Prompt("hello", "there")
    main += padding_label
    main += Label("here are some items", Label.ALIGN_LEFT, markup=False)

    splitter = Splitter()
    main += splitter
    splitter += ListView(
        ["hello", "tehre", "master", "kenobi"], align=Label.ALIGN_LEFT, padding=0
    )

    splitter += ListView(
        ["hello", "tehre", "master", "kenobi"], align=Label.ALIGN_CENTER, padding=0
    )

    splitter += ListView(
        ["hello", "tehre", "master", "kenobi"], align=Label.ALIGN_RIGHT, padding=0
    )

    progress = 0.6
    main += padding_label
    main += ProgressBar(progress_function=lambda: progress)
    main[-1].forced_width = 30

    main += padding_label
    main += InputField()

    main.select(0)
    main.center()
    main.print()

    while True:
        key = getch()

        # main[-1].send(key)
        # main.print()
        # continue

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
