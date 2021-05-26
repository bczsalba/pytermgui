"""
pytermgui.cmd
-----------------
author: bczsalba


This module provides the command-line capabilities of the module.
"""

import sys
from typing import Callable
from argparse import ArgumentParser, Namespace

from . import (
    Widget,
    Container,
    InputField,
    Prompt,
    Label,
    clear,
    bold,
    foreground as color,
    ansi_to_markup,
    markup_to_ansi,
    prettify_markup,
    getch,
    keys,
    real_length,
    alt_buffer,
    screen_size,
    cursor_up,
    cursor_right,
    report_cursor,
    move_cursor,
    screen_height,
    reset,
)


# depth is not used but is always provided
def prompt_label_style(depth: int, item: str) -> str:  # pylint: disable=unused-argument
    """Colorful prompt labels"""

    color_one = [
        "(",
        ")",
    ]

    color_two = [
        ":",
    ]

    out = ""
    for char in item:
        if char in color_one:
            out += color(bold(char), 157)

        elif char in color_two:
            out += color(bold(char), 210)

        else:
            out += color(char, 252)

    return out


# depth is not used but is always provided
def prompt_value_style(depth: int, item: str) -> str:  # pylint: disable=unused-argument
    """Colorful prompt_values"""

    if item == "None":
        col = 210
    elif item.isdigit():
        col = 157
    elif item.startswith("keys."):
        col = 210
    else:
        col = 157

    # mypy doesn't believe this to be str, so we have to be verbose.
    return str(bold(color(item, col)))


def color_call(col: int, set_bold: bool = False) -> Callable[[int, str], str]:
    """Create a color callable"""

    out: Callable[[int, str], str]

    # bold() and color() are typed to return str, but mypy can't read it
    if set_bold:
        out = lambda _, item: str(bold(color(item, col)))
    else:
        out = lambda _, item: str(color(item, col))

    return out


def key_info() -> None:
    """Show information about a keypress"""

    old = report_cursor()

    dialog = Container() + Label("press a key... ")
    for line in dialog.get_lines():
        print(line)

    # move cursor into "... >< "
    cursor_up(2)
    cursor_right(dialog.width - 3)
    sys.stdout.flush()

    user_key = getch(interrupts=False)
    move_cursor(old)

    # things get messy when the terminal scrolls at EOB
    if old[1] == screen_height():
        cursor_up(4)

    # get data
    printable = '"' + user_key.encode("unicode_escape").decode("utf-8") + '"'
    length = str(len(user_key))
    real_len = str(real_length(user_key))

    aka = "None"
    if user_key in keys.values():
        for key, value in keys.items():
            if value == user_key:
                aka = "keys." + key
                break

    output = Container()
    for label, value in [
        ("key:", printable),
        ("aka:", aka),
        ("len():", length),
        ("real_length():", real_len),
    ]:
        prompt = Prompt(label, value)
        prompt.width = 15 + max(len(printable), len(aka))
        prompt.set_char("delimiter", ["", ""])
        output += prompt

    for line in output.get_lines():
        print(line)


def parse_text(args: Namespace) -> None:
    """Parse input text"""

    txt = args.parse[0]

    if args.inverse:
        parsed = ansi_to_markup(txt)
        inverse_result = markup_to_ansi(parsed)
        parsed = prettify_markup(parsed)

    else:
        parsed = markup_to_ansi(txt)
        inverse_result = ansi_to_markup(parsed)
        txt = prettify_markup(txt)

    if args.escape:
        parsed = parsed.encode("unicode_escape").decode("utf-8")

    if args.no_container:
        print("input:", txt + reset())
        print("output:", parsed)
        sys.exit(0)

    display = (
        Container() + Label(txt + reset()) + Label("|") + Label("V") + Label(parsed)
    )

    if args.show_inverse:
        display += Label()
        display += Label("(" + inverse_result + ")")

    for line in display.get_lines():
        print(line)


def markup_writer() -> None:
    """An interactive program to write markup"""

    def create_container(obj: Widget, label: str, corners: list[str]) -> Container:
        """Create a container with the right attributes"""

        cont = Container(vert_align=Container.VERT_ALIGN_TOP)
        cont.forced_height = 12
        cont += obj

        chars = corners.copy()
        chars[0] += label
        cont.set_char("corner", chars)


        return cont

    cont = Container()
    cont += Label(markup_to_ansi(" [bold underline 67]Markup Live Editor[/] "))

    infield = InputField()
    view = Label("This will show a live view of your markup.", align=Label.ALIGN_LEFT)
    final = Label(align=Label.ALIGN_LEFT)

    corners = cont.get_char("corner")
    assert isinstance(corners, list)

    cont += create_container(infield, " editor ", corners)
    cont += create_container(view, " view ", corners)
    output = create_container(final, " output ", corners)

    cont.forced_width = 100
    cont.center()
    cont.focus()

    with alt_buffer():
        cont.print()

        while True:
            key = getch(interrupts=False)

            if key is keys.CTRL_C:
                break

            infield.send(key)

            try:
                new = infield.value.replace('\n', '[/]\n')
                view.value = markup_to_ansi(new)
                final.value = prettify_markup(new)

            except SyntaxError as error:
                view.value = bold(color("SyntaxError: ", 210)) + str(error)

            cont.print()

        clear()

        for widget in cont[1:]:
            cont.remove(widget)

        output.width = real_length(final.value) + output.sidelength
        cont += output
        output.align = Label.ALIGN_CENTER
        output.vert_align = Container.VERT_ALIGN_TOP

        cont.center()
        cont.print()
        getch()


def main() -> None:
    """Main function for command line things."""

    Container.set_char("border", ["│ ", "─", " │", "─"])
    Container.set_char("corner", ["╭", "╮", "╯", "╰"])
    Container.set_style("border", color_call(60, set_bold=True))
    Container.set_style("corner", color_call(60, set_bold=True))
    Prompt.set_style("label", prompt_label_style)
    Prompt.set_style("value", prompt_value_style)

    parser = ArgumentParser(
        prog="pytermgui",
        description="a command line utility for working with pytermgui.",
    )
    parser.add_argument("file", help="open a .ptg file", nargs="?")
    parser.add_argument(
        "-g", "--getch", help="print information about a keypress", action="store_true"
    )
    parser.add_argument(
        "--markup", help="open interactive markup editor", action="store_true"
    )
    parser.add_argument(
        "-p", "--parse", metavar=("txt"), help="parse markup->ansi", nargs=1
    )
    parser.add_argument("--inverse", help="parse ansi->markup", action="store_true")
    parser.add_argument(
        "--escape", help="escape parsed text output", action="store_true"
    )
    parser.add_argument(
        "--show-inverse",
        help="show result of inverse parse operation",
        action="store_true",
    )
    parser.add_argument(
        "--no-container",
        help="show getch/parse output without a container surrounding it",
        action="store_true",
    )
    parser.add_argument(
        "--size",
        help="print current terminal size as {rows}x{cols}",
        action="store_true",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.getch:
        key_info()

    elif args.markup:
        markup_writer()

    elif args.parse:
        parse_text(args)

    elif args.size:
        rows, cols = screen_size()
        print(f"{rows}x{cols}")

    elif args.file:
        try:
            with open(args.file, "r") as ptg_file:
                print("this is currently not supported.")
                ptg_file.readlines()

        except Exception as error:  # pylint: disable=broad-except
            print(f'pytermgui: Could not open file "{args.file}": {error}')
