"""
pytermgui.cmd
-----------------
author: bczsalba


This module provides the command-line capabilities of the module.
"""

import sys
from typing import cast
from argparse import ArgumentParser

from . import (
    MarkupFormatter,
    WindowManager,
    real_length,
    Container,
    Splitter,
    Window,
    boxes,
    keys,
)


def show_getch() -> None:
    """Print a container with the getch output"""

    def _show_output(key: str) -> None:
        """Show output in a Container"""

        name = keys.get_name(key)
        if name is not None:
            name = "keys." + name
        else:
            name = ascii(key)

        root = (
            Container(forced_width=35)
            + {"[252]key[/fg][210]:": "[wm-section]" + name}
            + {"[252]len[157]()[210]:": "[wm-section]" + str(len(key))}
            + {"[252]real_length[157]()[210]:": "[wm-section]" + str(real_length(key))}
        )

        for line in root.get_lines():
            print(line)

    Splitter.set_char("separator", "  ")
    boxes.DOUBLE_TOP.set_chars_of(Container)
    boxes.DOUBLE_TOP.set_chars_of(Window)

    border_corner = MarkupFormatter("[60 bold]{item}")
    for cls in [Container, Window]:
        cls.set_style("border", border_corner)
        cls.set_style("corner", border_corner)

    with WindowManager() as manager:

        def _handle_keypress(window: Window, key: str) -> None:
            """Handle keypress, call method if non-mouse"""

            if manager.mouse_handler(key) is None:
                manager.stop()
                window.output_key = key

        window = cast(
            Window,
            (Window() + "[wm-title]Press a key!").center(),
        )

        window.bind(keys.ANY_KEY, _handle_keypress)

        manager.add(window)
        manager.run()

    _show_output(window.output_key)


def main() -> None:
    """Main method"""

    parser = ArgumentParser()
    parser.add_argument(
        "-g",
        "--getch",
        action="store_true",
        help="Get and print a keyboard input",
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.getch:
        show_getch()


if __name__ == "__main__":
    main()
