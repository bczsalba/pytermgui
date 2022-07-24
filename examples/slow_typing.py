"""This file details implementing a more advanced macro.

Using this macro, you can have an animation mimicking someone
typing a message out.

It uses a factory-like pattern, where new macros are defined
on-demand, allowing for use of multiple different typing animations
on one screen.
"""

from __future__ import annotations

import time

import pytermgui as ptg


def define_slow_macro(
    ms_per_char: int = 100, lang: ptg.MarkupLanguage = ptg.tim
) -> str:
    """Defines a slow typer macro, returns its name.
    Args:
        ms_per_char: How many milliseconds should pass between each
            char being displayed.
        lang: The markup language to define the new macro on.

    Returns:
        The name of the newly defined macro. The name follows the form:
            `slow12345`
        ...where `12345` is the last 5 characters of the current `time.time()`.
    """

    start = time.time()

    def _macro(text: str) -> str:
        current = time.time()
        char_count = (current - start) / (ms_per_char / 1000)

        trimmed = text[: round(char_count)]

        if int(current) % 2 == 0:
            return trimmed + "█"

        return trimmed

    name = f"!slow{str(time.time())[-5:]}"
    lang.define(name, _macro)
    return name


with ptg.WindowManager() as manager:
    slow1 = define_slow_macro()
    time.sleep(0.1)
    slow2 = define_slow_macro()

    manager.add(
        ptg.Window(
            ptg.Label(
                f"[210 bold {slow1}]This is a very long message...",
                parent_align=0,
            ),
            ptg.Label(f"[{slow2}]This is a very long message...", parent_align=0),
            width=50,
        )
    )
