"""
pytermgui.cmd
-----------------
author: bczsalba


This module provides the command-line capabilities of the module.
"""

from sys import argv
from typing import Any

from . import (
    __version__,
    getch,
    keys,
    Prompt,
    cursor_up,
    real_length,
)

HELP = f"""\
pytermgui v{__version__}:

    ptg <path>
        - currently not implemented

    ptg -g/--getch
        - print information about key press

"""


def get_value_from_prompt(prompt: Prompt, label: str, value: str) -> Any:
    """Get value from a prompt object"""

    prompt.label = label
    prompt.value = value
    return prompt.get_lines()[0]


def main() -> None:
    """Main function for command line things."""

    args = argv[1:]

    if len(args) == 0:
        print(HELP)

    elif args[0] == "-g" or args[0] == "--getch":
        print("press a key...")
        cursor_up()
        user_key = getch()

        printable = '"' + user_key.encode("unicode_escape").decode("utf-8") + '"'
        _len = str(len(user_key))
        _real_len = str(real_length(user_key))

        prompt = Prompt()
        prompt.set_char("delimiter", ["", ""])

        from_keys = "None"
        if user_key in keys.values():
            for key, value in keys.items():
                if value == user_key:
                    from_keys = "keys." + key

        prompt.width = 15 + max(len(printable), len(from_keys))

        print(get_value_from_prompt(prompt, "key:", printable))
        print(get_value_from_prompt(prompt, "aka:", from_keys))
        print(get_value_from_prompt(prompt, "len():", _len))
        print(get_value_from_prompt(prompt, "real_length():", _real_len))

    else:
        print(HELP)
