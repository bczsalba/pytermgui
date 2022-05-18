"""This module calls `install()` on import, and defines `print` as `pprint`.

It allows setting up pretty print functionality in only one line.

Usage:
    ```python3
    >>> from pytermgui.pretty import print
    ```
"""

from __future__ import annotations

import os
import sys
import builtins
from typing import Any

from .parser import tim
from .prettifiers import prettify
from .terminal import get_terminal

try:
    # Try to get IPython instance. This function is provided by the
    # IPython runtime, so if running outside of that context a NameError
    # is raised.
    IPYTHON = get_ipython()  # type: ignore
    from IPython.core.formatters import BaseFormatter  # pylint: disable=import-error

except NameError:
    IPYTHON = None
    BaseFormatter = object


NO_WELCOME = (
    os.getenv("PTG_SILENCE_PRETTY") is not None or not get_terminal().is_interactive()
)

__all__ = ["pprint", "install"]


def pprint(
    *items: Any,
    indent: int = 2,
    expand_all: bool = False,
    force_markup: bool = False,
    parse: bool = True,
    **print_args: Any,
) -> None:
    r"""A wrapper to pretty-print any object.

    This essentially just calls `prettify` on each given object, and passes the
    `**print_args` right through to print. Note that when the `sep` print argument is
    ommitted it is manually set to ", \n".

    To customize any of the styles, see `MarkupLanguage.prettify`.

    Args:
        *items: The items to print. These are passed in the same way they would be into
            builtin print.
        indent: The indentation value used for multi-line objects. This is ignored when
            the given object has a `len() < 2`, and `expand_all is not set.`
        force_tim: Turn all ANSI-sequences into tim before pretty printing.
        expand_all: Force-expand containers, even when they would normally be collapsed.
        **print_args: All arguments passed to builtin print.
    """

    if "sep" not in print_args:
        print_args["sep"] = ", \n"

    pretty = []
    for item in items:
        pretty.append(
            prettify(
                item,
                force_markup=force_markup,
                indent=indent,
                expand_all=expand_all,
                parse=parse,
            )
        )

    get_terminal().print(*pretty, **print_args)


def install(
    indent: int = 2, force_markup: bool = False, expand_all: bool = False
) -> None:
    """Sets up `pprint` to print all REPL output. IPython is also supported.

    This functions sets up a hook that will call `pprint` after every interactive
    return. The given arguments are passed directly to `pprint`, so for more information
    you can check out that function.

    Usage is pretty simple:

    ```python3
    >>> from pytermgui import pretty
    >>> tim.setup_displayhook()
    >>> # Any function output will now be prettified
    ```

    ...or alternatively, you can import `print` from `pytermgui.pretty`,
    and have it automatically set up, and replace your namespace's `print`
    function with `tim.pprint`:

    ```python3
    >>> from pytermgui.pretty import print
    ... # Under the hood, the above is called and `tim.pprint` is set
    ... # for the `print` name
    >>> # Any function output will now be prettified
    ```

    Args:
        indent: The indentation value used for multi-line objects. This is ignored when
            the given object has a `len() < 2`, and `expand_all is not set.`
        force_tim: Turn all ANSI-sequences into tim before pretty printing.
        expand_all: Force-expand containers, even when they would normally be collapsed.
    """

    def _hook(value: Any) -> None:
        if value is None:
            return

        pprint(value, force_markup=force_markup, indent=indent, expand_all=expand_all)

        # Sets up "_" as a way to access return value,
        # inkeeping with sys.displayhook
        builtins._ = value  # type: ignore

    if IPYTHON is not None:
        IPYTHON.display_formatter.formatters["text/plain"] = PTGFormatter(
            force_markup=force_markup, indent=indent, expand_all=expand_all
        )

    else:
        sys.displayhook = _hook

    if not NO_WELCOME:
        with get_terminal().no_record():
            print()
            tim.print("[113 bold]Successfully set up prettification!")
            tim.print("[245 italic]> All function returns will now be pretty-printed,")
            print()
            pprint("[245 italic]Including [/italic 210]Markup!")
            print()

    get_terminal().displayhook_installed = True


class PTGFormatter(BaseFormatter):  # pylint: disable=too-few-public-methods
    """An IPython formatter for PTG pretty printing."""

    def __init__(self, **kwargs: Any) -> None:
        """Initializes PTGFormatter, storing **kwargs."""

        super().__init__()

        self.kwargs = kwargs

    def __call__(self, value: Any) -> None:
        """Pretty prints the given value, as well as a leading newline.

        The newline is needed since IPython output is prepended with
        "Out[i]:", and it might mess alignments up.
        """

        print("\n")
        pprint(value, **self.kwargs)

        # Sets up "_" as a way to access return value,
        # inkeeping with sys.displayhook
        builtins._ = value  # type: ignore


# I am normally violently against shadowing builtins, but this is an optional,
# (hopefully always) REPL-only name, only provided for convenience.
print = pprint  # pylint: disable=redefined-builtin

install()
