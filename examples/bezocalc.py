"""
pytermgui/examples/bezocalc.py
------------------------------
author: bczsalba


Ever wondered what the top billionaires' wealth would
amount to in terms of BEZO, an imaginary currency mirroring
the net-worth of Jeff Bezos?

Probably not. Here is a program showing it anyways."""

import os
from time import sleep
from enum import Enum, auto
from dataclasses import dataclass
from typing import Union, Optional

import requests
from fuzzywuzzy import fuzz
from pytermgui import (
    Widget,
    Container,
    Splitter,
    Label,
    InputField,
    serializer,
    cursor_at,
    strip_ansi,
    getch,
    boxes,
    alt_buffer,
    foreground,
    background,
    markup_to_ansi,
    real_length,
    keys,
    cursor_home,
    get_widget,
)

LAYOUT_DIR = "layouts"

LOADING_ART = fr"""
[bold 210] _-_ 
[bold 210]/ [249]o[210] \
[bold 222]\ [249]x[222] /
[bold 237]/\|/\

loading..."""


def to_local(path: str):
    """Return path joined with local (to file) path"""

    return os.path.join(os.path.dirname(__file__), path)


class Gender(Enum):
    """Enum for gender information, other can be represented as a string."""

    MALE = auto()
    FEMALE = auto()


@dataclass
class Person:
    """Simple dataclass to store information on a person"""

    name: str
    worth: float
    gender: Union[str, Gender]


def simplify_float(data: float) -> Union[int, float]:
    """Remove trailing 0 from a float"""

    return int(data) if data.is_integer() else data


def get_people(limit: Optional[int] = None) -> list[Person]:
    """Get a list of the top `limit` of Person"""

    api_url = "https://forbes400.herokuapp.com/api/forbes400?limit="
    if limit is not None:
        api_url += str(limit)

    response = requests.get(api_url).json()

    people: list[Person] = []
    gender: Union[Gender, str]

    for element in response:
        if not "gender" in element:
            gender = "N/A"

        elif element["gender"] == "M":
            gender = Gender.MALE

        elif element["gender"] == "F":
            gender = Gender.FEMALE

        else:
            gender = element["gender"]

        people.append(
            Person(element["personName"], int(element["finalWorth"]) / 1000, gender)
        )

    return people


def fade_widget(widget: Widget, out: bool = False) -> None:
    colors = [238, 236, 234]
    if out:
        colors.reverse()

    lines = widget.get_lines()
    for color in colors:
        with cursor_at(widget.pos) as print_widget:
            for line in lines:
                print_widget(foreground(strip_ansi(line), color))

            sleep(1 / 20)


def outer_container():
    """Return an outer-styled Container()"""

    cont = Container()
    cont.set_style("border", lambda depth, item: foreground(item, 239))
    cont.set_style("corner", lambda depth, item: foreground(item, 239))

    return cont


def generate_layout():
    """Generate home screen layout"""

    boxes.DOUBLE_TOP.set_chars_of(Container)
    Container.set_style("border", lambda depth, item: foreground(item, 234))
    Container.set_style("corner", lambda depth, item: foreground(item, 234))
    Splitter.set_style("separator", lambda depth, item: foreground(item, 234))
    Splitter.set_char("separator", boxes.DOUBLE_TOP.borders[0])

    corners = boxes.DOUBLE_TOP.corners.copy()
    corners[0] += " bezo "
    corners[1] = " calc " + corners[1]
    root = outer_container()
    root.set_char("corner", corners)
    root.forced_height = 32
    # root.width = 130
    root.vert_align = Container.VERT_ALIGN_TOP

    header = Container() + Label("title")
    header[-1].id = "header_title"
    root += header

    inner = Container()
    inner.id = "inner"
    inner_title = (
        Splitter("39;36;36")
        + Label("[242 bold]Name:")
        + Label("[242 bold]Worth in dollars:")
        + Label("[242 bold]Worth in Bezos:")
    )
    inner_title.id = "inner_title"
    inner += inner_title

    for i in range(24):
        row = Splitter("39;36;36")
        if i > 0:
            row.id = f"inner_row{i - 1}"

        row += Label("[221] ", align=Label.ALIGN_LEFT)
        row += Label("[157 bold] ")
        row += Label("[214 bold] ")
        inner += row

    root += inner

    root += Label()
    field = InputField(prompt=" ")
    field.id = "field"
    root += field

    with open(to_local(LAYOUT_DIR + "/bezos.ptg"), "w") as datafile:
        serializer.dump_to_file(root, datafile)


def help_menu(root: Container) -> None:
    """A menu to display various commands"""

    commands = [
        ("help, ?", "show help menu"),
        ("search, /", "search for a person "),
        ("convert, $", "convert between USD and BEZO"),
    ]

    help_root = outer_container()
    help_root += Label("[bold 72]Help Menu")

    help_inner = Container()
    help_root += help_inner

    for name, text in commands:
        row = Splitter()
        row.arrangement = "20;30"

        row += Label("[157]" + name, align=Label.ALIGN_LEFT)
        row += Label("[italic 239]" + text, align=Label.ALIGN_RIGHT)
        help_inner += row

    fade_widget(root)

    help_root.center()
    help_root.print()
    getch()

    fade_widget(root, True)


def convert_menu(root: Container, bezo: int) -> None:
    """A menu to convert between BEZO and USD"""

    convert_root = outer_container()
    convert_root.forced_width = 70
    convert_root += Label("[bold 72]Convert Menu")

    convert_inner = Container()
    convert_root += convert_inner

    for name in ["[157]$USD", "[208]BEZO"]:
        row = Splitter("6;50")
        row += Label(name)
        row += InputField()
        convert_inner += row

    result_row = Splitter("6;50")
    result_row += Label("[bold 214]Result")
    result_row += Label()

    fade_widget(root)

    fields = [row[1] for row in convert_inner]
    focused = fields[0]
    focused.focus()

    convert_root.center()
    convert_root.print()

    while True:
        key = getch()

        if key == keys.TAB:
            focused.blur()
            focused = fields[len(fields) - fields.index(focused) - 1]
            focused.focus()

        elif key == keys.RETURN:
            value = focused.clear_value()
            if not value.isdigit() or int(value) == 0:
                return

            # USD -> BEZO
            if focused == fields[0]:
                converted = int(value) / (bezo * 10 ** 6)
                text = f"[249]${value} converts to B{simplify_float(converted):,}!"

            # BEZO -> USD
            elif focused == fields[1]:
                converted = bezo * int(value) * 10 ** 6
                text = f"[249]B{value} converts to ${simplify_float(converted):,}!"

            focused.blur()
            result_row[1].value = text
            convert_inner += result_row
            convert_root.print()
            getch()

            focused.focus()
            convert_root.wipe()
            convert_inner.pop(-1)

        elif key == keys.ESC:
            break

        else:
            focused.send(key)

        convert_root.print()

    fade_widget(root, True)


def search_menu(people: list[Person], field: InputField, bezo: int) -> None:
    """A menu that overlays root to show filtered results"""

    def _update_search(value: str, inner: Container, root: Container) -> None:
        """Update inner values based on search"""

        ratios = []
        for person in people:
            ratios.append([person, fuzz.ratio(value, person.name)])

        ratios.sort(key=lambda item: item[1], reverse=True)
        data = [person for person, ratio in ratios if ratio > 30]

        # the first line is the title, second is padding
        for row in inner[2:]:
            for label in row:
                label.value = ""

        for row, person in zip(inner[2:], data):
            name, usd, bezo_label = row
            name.value = name_pre + person.name
            usd.value = usd_pre + f"$ [/bold 246]{person.worth:0<7,} billion"
            bezo_label.value = (
                bezo_pre + f"B [/bold 246]{round(person.worth/bezo, 2):0<4,}"
            )

        root.print()

    with open(to_local(LAYOUT_DIR + "/bezos.ptg"), "r") as file:
        s_root = serializer.load_from_file(file)

    # Note: this overwrites the "field" id established in main()
    #       there should be an object-local get to combat this.
    s_inner = get_widget("inner")
    s_field = get_widget("field")
    s_title = get_widget("header_title")

    s_field.set_style("cursor", lambda depth, item: background(item, 72))
    s_field.prompt = " /"
    s_field.value = field.value[1:]
    s_field.cursor = field.cursor
    s_title.value = "[bold 208]Search for a person!"
    name_pre, usd_pre, bezo_pre = [label.value.strip() for label in s_inner[3]]

    s_root.focus()
    s_root.center()
    s_root.print()

    while True:
        key = getch()

        if key == keys.RETURN:
            return

        if real_length(s_field.get_value()) == 0 and key == keys.BACKSPACE:
            field.clear_value()
            break

        if key == keys.ESC:
            field.clear_value()
            break

        s_field.send(key)
        value = s_field.get_value()

        _update_search(value, s_inner, s_root)


def main():
    """Where the magic happens"""

    with open(to_local(LAYOUT_DIR + "/bezos.ptg"), "r") as datafile:
        root = serializer.load_from_file(datafile)

    field = get_widget("field")
    field.set_style("cursor", lambda depth, item: background(item, 72))
    title = get_widget("header_title")
    title.value = "[bold 208]What are they worth?"

    inner = get_widget("inner")
    loading = outer_container() + Label(LOADING_ART)
    loading.center()
    loading.print()

    people = get_people()
    bezo = 0
    for person in people:
        if person.name == "Jeff Bezos":
            bezo = person.worth

    loading.wipe()

    for row, person in zip(inner[2:], people):
        name, dollars, bezos = row
        name.value = name.value[:-1] + person.name
        dollars.value = dollars.value[:-1] + f"$ [/bold 246]{person.worth:0<7,} billion"
        bezos.value = (
            bezos.value[:-1] + f"B [/bold 246]{round(person.worth/bezo, 2):0<4,}"
        )

    root.focus()
    root.center()
    root.print()

    while True:
        root.print()

        key = getch(interrupts=False)
        if key == chr(3):
            break

        command = field.get_value()
        if not key == keys.RETURN:
            if key == "?":
                help_menu(root)
                continue

            elif key == "$":
                convert_menu(root, bezo)
                continue

            field.send(key)
            root.print()

            if not command.startswith("/"):
                continue

        if command == "exit":
            break

        if command in ["help", "?"]:
            help_menu(root)
            field.clear_value()

        elif command == "convert":
            convert_menu(root, bezo)
            field.clear_value()

        elif command.startswith("/"):
            search_menu(people, field, bezo)


if __name__ == "__main__":
    if not os.path.exists(to_local(LAYOUT_DIR)):
        os.mkdir(to_local(LAYOUT_DIR))
    generate_layout()

    with alt_buffer(cursor=False):
        main()

    print(markup_to_ansi("[bold @234 208] Goodbye! "))
