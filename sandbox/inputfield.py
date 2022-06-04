from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytermgui as ptg


def _process_arguments(argv: list[str] | None = None) -> Namespace:
    """Processes command line arguments.

    Note that you don't _have to_ use the bultin argparse module for this; it
    is just what the module uses.

    Args:
        argv: A list of command line arguments, not including the binary path
            (sys.argv[0]).
    """

    parser = ArgumentParser(description="A simple text editor.")
    parser.add_argument("file", help="The file to read.", type=Path, nargs="?")
    parser.add_argument(
        "-s",
        "--string",
        help="String to edit, when file is not given.",
        metavar="STR",
    )

    parser.add_argument(
        "--highlight", action="store_true", help="Enable Python syntax highlighting."
    )

    return parser.parse_args(argv)


def _create_aliases() -> None:
    """Creates all the TIM aliases used by the application."""

    ptg.tim.alias("editor.header", "@157 240")
    ptg.tim.alias("editor.footer", "inverse editor.header")


def _configure_widgets() -> None:
    """Defines all the global widget configurations."""

    ptg.boxes.EMPTY.set_chars_of(ptg.Window)
    ptg.Splitter.set_char("separator", "")


def _define_layout() -> ptg.Layout:
    """Defines the application layout."""

    layout = ptg.Layout()

    layout.add_slot("Header", height=1)
    layout.add_break()

    layout.add_slot("Body")
    layout.add_break()

    layout.add_slot("Footer", height=1)

    return layout


def get_watcher(obj: object, *attrs: str | tuple[str, str]) -> Callable[[str], str]:
    """Creates a macro callable for retrieving attributes of an object.

    Args:
        obj: The object to get attributes of.
        *attrs: The name of the attributes to look at. Each attribute is looked
            up with using getattr, and the given name will be formatted into the
            template when the macro is called.

    Example of usage:

        field = InputField()
        tim.define("!cursor", get_watcher(field.cursor, "row", "col"))
        tim.print("[!cursor]Cursor: {row}:{col}")

    """

    valid_attrs = []
    for attr in attrs:
        if isinstance(attr, str):
            valid_attrs.append((attr, attr))
            continue

        alias, real = attr
        valid_attrs.append((alias, real))

    def _macro(fmt: str) -> None:
        try:
            return fmt.format(
                **{alias: getattr(obj, real) for alias, real in valid_attrs}
            )
        except Exception as err:
            return str(err)

    return _macro


def _read_content(path: Path) -> str:
    with open(path, "r") as file:
        return file.read()


def main(argv: list[str] | None = None, tim: ptg.MarkupLanguage = ptg.tim) -> None:
    """Runs the application."""

    _create_aliases()
    _configure_widgets()

    args = _process_arguments(argv)

    if args.file is not None:
        content = _read_content(args.file).replace("[", r"\[")

    elif args.string is not None:
        content = args.string.replace("[", r"\[")

    else:
        print("Please provide either a file or a string to edit.")
        return

    field = ptg.InputField(content, multiline=True)
    if args.highlight:
        field.styles.value = lambda _, text: ptg.tim.parse(ptg.highlight_python(text))

    tim.define("!cursor", get_watcher(field.cursor, "row", "col"))
    tim.define("!select_len", get_watcher(field, ("select_len", "_selection_length")))
    tim.define("!select_text", get_watcher(field, ("select_text", "selection")))

    with ptg.WindowManager() as manager:
        manager.layout = _define_layout()

        header = ptg.Window("[editor.header bold]Code Editor", box="EMPTY")
        header.styles.fill = "editor.header"

        footer = ptg.Window(
            ptg.Splitter(
                ptg.Label(
                    "[editor.footer !cursor] Cursor: {row}:{col}"
                    + " // [/!cursor !select_len]{select_len}",
                    parent_align=0,
                ),
                ptg.Label(
                    "[editor.footer !select_text]{select_text}",
                    parent_align=2,
                ),
            ).styles(fill="editor.footer"),
            box="EMPTY",
        )
        footer.styles.fill = "editor.footer"

        body = ptg.Window(field, overflow=ptg.Overflow.SCROLL)

        manager.add(header, assign="header")
        manager.add(body, assign="body")
        manager.add(footer, assign="footer")


if __name__ == "__main__":
    main(sys.argv[1:])
