"""
pytermgui/examples/readme.py
----------------------------
author: bczsalba

A simple examplary program that creates thing
"""

from pytermgui import (
    Container,
    Splitter,
    Label,
    Prompt,
    InputField,
    ListView,
    MarkupFormatter,
    clear,
    keys,
    boxes,
    getch,
    alt_buffer,
    get_widget,
    markup_to_ansi,
    strip_ansi,
)
from pytermgui.parser import NAMES as parser_names

def setup() -> Container:
    """Create all the objects for the menu, return root"""

    boxes.DOUBLE_TOP.set_chars_of(Container)
    outline_formatter = MarkupFormatter("[245]{item}")

    Container.set_style("border", outline_formatter)
    Container.set_style("corner", outline_formatter)
    Splitter.set_style("separator", outline_formatter)
    root = Container() + Label("[141 bold]Enter a color![/]") + Label()

    options = []
    for name in parser_names:
        options.append(f"[245 {name}]{name}[/]")

    options += [
        "",
        "[245]0-255",
        "[245]#rrbbgg",
        "[245]rrr;bbb;ggg",
        "",
        "[245]/fg",
        "[245]/bg",
        "[245]/{tag}",
    ]

    listview = ListView(options=options, align=Label.ALIGN_RIGHT)
    listview.set_char('delimiter', [''] * 2)
    hint_container = Container() + listview
    hint_container.forced_width = 20

    field_container = Container(vert_align=Container.VERT_ALIGN_TOP) + InputField()
    field_container[0].id = "field"
    field_container.forced_height = hint_container.height - 2
    field_container.forced_width = 60

    splitter = Splitter() + field_container + hint_container
    splitter.set_char('separator', " " + root.get_char('border')[0])

    inner = Container() + splitter
    root += inner

    result_label = Label(align=Label.ALIGN_LEFT)
    result_label.id = "result"
    result_label.set_style('value', lambda _, item: item)
    result_container = Container() + result_label
    root += result_container

    field_container.focus()
    return root

def input_loop(root: Container) -> str:
    """Handle inputs for `root`"""

    field = get_widget("field")
    result = get_widget("result")
    
    root.print()
    while True:
        key = getch(interrupts=False)
        if key == chr(3):
            return field.get_value()

        if key == keys.CTRL_L:
            clear()
            root.print()
            continue

        field.send(key)

        try:
            value = field.get_value(strip=False).replace("\n", "[/]")
            result.value = markup_to_ansi(value)

        except Exception as error:
            name = type(error).__name__

            result.value = (
                markup_to_ansi(f"[210 bold]{name}[/fg][/]") 
            )


        root.print()

if __name__ == "__main__":
    root = setup()
    root.center()

    with alt_buffer(cursor=False):
        output = input_loop(root)

    print(output)
