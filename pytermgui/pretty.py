"""This module sets up `markup.setup_displayhook` on import, and defines `print` as `markup.pprint`.

It allows setting up pretty print functionality in only one line.

Usage:
    ```python3
    >>> from pytermgui.pretty import print
    ```
"""

from pytermgui import markup


markup.setup_displayhook()

with markup as mprint:
    mprint()
    mprint("[113 bold]Successfully set up prettification!")
    mprint("[245 italic]> All function returns will now be pretty-printed,")
    mprint()
    markup.pprint("[245 italic]Including [/italic 210]Markup!")
    mprint()

# I am normally violently against shadowing builtins, but this is an optional,
# (hopefully always) REPL-only name, only provided for convenience.
print = markup.pprint  # pylint: disable=redefined-builtin
