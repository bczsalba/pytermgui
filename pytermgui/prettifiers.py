"""This module provides some methods to prettify things.

The main export here is `prettify`. It uses `pytermgui.parser.tim`, and all of its
markup magic to create prettier representations of whatever is given.
"""

import builtins
from typing import Any

from .parser import RE_ANSI, RE_MARKUP, tim
from .exceptions import MarkupSyntaxError, AnsiSyntaxError


__all__ = ["prettify"]


def _prettify_container(
    target, indent: int, expand_all: bool, force_markup: bool
) -> str:
    """Prettifies a builtin container.

    All arguments are analogous to `prettify`.

    Returns:
        Pretty string markup.
    """

    if len(target) < 2 and not expand_all:
        indent = 0

    chars = str(target)[0], str(target)[-1]
    buff = chars[0]

    indent_str = ("\n" if indent > 0 else "") + indent * " "

    if isinstance(target, dict):
        for i, (key, value) in enumerate(target.items()):
            if i > 0:
                buff += ", "

            buff += indent_str
            buff += prettify(key, indent=0, parse=False) + ": "

            pretty = prettify(
                value,
                indent=indent,
                expand_all=expand_all,
                force_markup=force_markup,
                parse=False,
            )

            lines = pretty.splitlines()
            buff += lines[0]
            for line in lines[1:]:
                buff += indent_str + line

    else:
        for i, item in enumerate(target):
            if i > 0:
                buff += ", "

            pretty = prettify(
                item,
                indent=indent,
                expand_all=expand_all,
                force_markup=force_markup,
                parse=False,
            )

            for line in pretty.splitlines():
                buff += indent_str + line

    if indent > 0:
        buff += ",\n"

    return buff + chars[1]


def _prettify_str(target, force_markup=True) -> str:
    """Prettifies a string.

    All arguments are analogous to `prettify`.

    Returns:
        Pretty string markup.
    """

    buff = ""
    if len(RE_ANSI.findall(target)) > 0:
        if not force_markup:
            return target

        target = tim.get_markup(target)

    old_raise_markup = tim.raise_unknown_markup
    tim.raise_unknown_markup = True

    if len(RE_MARKUP.findall(target)) > 0:
        try:
            buff = "'" + tim.get_markup(tim.prettify_markup(target)) + "'"

        except MarkupSyntaxError:
            target = target.replace("[", r"\[")

    tim.raise_unknown_markup = old_raise_markup

    if buff == "":
        sanitized = target.replace("\x1b", "\\x1b")
        buff = f"[pprint-str]'{sanitized}'"

    return buff + "[/]"


def prettify(
    target: Any,
    indent: int = 2,
    force_markup: bool = False,
    expand_all: bool = False,
    parse: bool = True,
) -> str:
    """Prettifies any Python object.

    This uses a set of pre-defined aliases for the styling, and as such is fully
    customizable.

    The aliases are:
    - `pprint-str`: Applied to all strings, so long as they do not contain TIM code.
    - `pprint-int`: Applied to all integers and booleans. The latter are included as
        they subclass int.
    - `pprint-type`: Applied to all types.
    - `pprint-none`: Applied to NoneType. Note that when using `pytermgui.pretty`, a
        single `None` return value will not be printed, only when part of a more
        complex structure.

    Args:
        target: The object to prettify. Can be any type.
        indent: The indentation used for multi-line objects, like containers. When
            set to 0, these will be collapsed. By default, container types with
            `len() == 1` are always collapsed, regardless of this value. See
            `expand_all` to overwrite that behaviour.
        force_markup: When this is set every ANSI-sequence string will be turned
            into markup and syntax highlighted.
        expand_all: When set, objects that would normally be force-collapsed are
            also going to be expanded.
        parse: If not set, the return value will be a plain markup string, not yet
            parsed.

    Returns:
        A pretty string of the given target.
    """

    if target in dir(builtins) and not target.startswith("__"):
        target = builtins.__dict__[target]

    buff = ""
    if isinstance(target, (list, dict, set, tuple)):
        buff = _prettify_container(
            target, indent=indent, expand_all=expand_all, force_markup=force_markup
        )

    elif isinstance(target, str):
        buff = _prettify_str(target, force_markup=force_markup)

    elif isinstance(target, int):
        buff = f"[pprint-int]{target}[/]"

    elif isinstance(target, type):
        buff = f"[pprint-type]{target.__name__}[/]"

    elif target is None:
        buff = f"[pprint-none]{target}[/]"

    else:
        return str(target)

    if parse:
        try:
            return tim.parse(buff)
        except (AnsiSyntaxError, MarkupSyntaxError):
            pass

    return str(buff) or str(target)
