#!/usr/bin/env python3
"""Common commands for the kitty terminal emulator

Kitty allows remote control if the proper flag is set in config.
This lets users configure settings on the fly, using some
commands. These commands tend to be a bit too long to quickly type
out, so this utility creates a frontend to manage them.

The currently supported commands are:
- kitty @ set-window-title {title} : Set OS window's title
- kitty @ resize-os-window --width {width}: Set OS window's width
- kitty @ resize-os-window --height {height}: Set OS window's height
"""

from subprocess import run

from argparse import ArgumentParser, Namespace
import pytermgui as ptg


CONFIG_YAML = """\
config:
    InputField:
        styles:
            fill: '[@236]{item}'
            value: '[72]{item}'

    Window:
        styles:
            border: &border-style '[60]{item}'
            corner: *border-style

    Button:
        styles:
            label: '[@236 72 bold]{item}'

    Splitter:
        chars:
            separator: "  "
"""

COMMANDS = {
    "title": ["kitty", "@", "set-window-title"],
    "width": ["kitty", "@", "resize-os-window", "--width"],
    "height": ["kitty", "@", "resize-os-window", "--height"],
}


def input_box(title: str, command: list) -> ptg.Container:
    """Create a Container with title, containing an InputField"""

    box = ptg.Container()
    box.set_char("corner", ["x- " + title + " -", "x", "x", "x"])
    box.set_char("border", ["| ", "-", " |", "-"])

    style = ptg.MarkupFormatter("[243]{item}")
    box.set_style("border", style)
    box.set_style("corner", style)

    field = ptg.InputField()
    field.bind(ptg.keys.RETURN, lambda field, _: run(command + [field.value]))
    box += field
    return box


def execute_all(window: ptg.Window) -> None:
    """Execute all `RETURN` bindings in window"""

    for field, _ in window.selectables:
        if not isinstance(field, ptg.InputField):
            continue

        field.execute_binding(ptg.keys.RETURN)


def parse_arguments() -> Namespace:
    """Parse command line arguments"""

    parser = ArgumentParser()
    parser.add_argument("-t", "--title", help="Set window title")
    parser.add_argument("-w", "--width", help="Set window width")
    parser.add_argument("--height", help="Set window height")

    return parser.parse_args()


def main() -> None:
    """Main method"""

    args = parse_arguments()
    no_tui = bool(args.title) | bool(args.width) | bool(args.height)

    if args.title:
        run(COMMANDS["title"] + [args.title])

    if args.width:
        run(COMMANDS["width"] + [args.width])

    if args.height:
        run(COMMANDS["height"] + [args.height])

    if no_tui:
        return

    with ptg.WindowManager() as manager:
        loader = ptg.YamlLoader()
        namespace = loader.load(CONFIG_YAML)

        window = (
            ptg.Window(width=70)
            + "[210 bold]Kitty Remote"
            + "[210 bold]------------"
            + ""
            + ptg.Label(
                "[240 italic]> Press RETURN to run each command", parent_align=0
            )
            + ""
            + input_box("Title", COMMANDS["title"])
            + ""
            + (
                input_box("Width", COMMANDS["width"]),
                input_box("Height", COMMANDS["height"]),
            )
            + ""
            + ptg.Button("Submit all!", lambda *_: execute_all(window))
        ).center()

        window.box = "DOUBLE"
        manager.add(window)

        manager.run()


if __name__ == "__main__":
    main()
