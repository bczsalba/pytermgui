"""This module provides some methods to prettify things.

The main export here is `prettify`. It uses `pytermgui.parser.tim`, and all of its
markup magic to create prettier representations of whatever is given.
"""

from __future__ import annotations

from collections import UserDict, UserList
from typing import Any

from .parser import RE_MARKUP, tim
from .highlighters import highlight_python
from .fancy_repr import supports_fancy_repr, build_fancy_repr


__all__ = ["prettify"]

CONTAINER_TYPES = (list, dict, set, tuple, UserDict, UserList)


# Note: This function can be optimized in a lot of ways, primarily the way containers
#       are treated.
def prettify(  # pylint: disable=too-many-branches
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
    - `str`: Applied to all strings, so long as they do not contain TIM code.
    - `int`: Applied to all integers and booleans. The latter are included as they
        subclass int.
    - `type`: Applied to all types.
    - `none`: Applied to NoneType. Note that when using `pytermgui.pretty`, a
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

    if isinstance(target, str):
        if RE_MARKUP.match(target) is not None:
            if parse:
                return f'"{tim.prettify_markup(target)}"'

            return target + "[/]"

        target = repr(target)

    if isinstance(target, CONTAINER_TYPES):
        if len(target) < 2 and not expand_all:
            indent = 0

        indent_str = ("\n" if indent > 0 else "") + indent * " "

        chars = str(target)[0], str(target)[-1]
        buff = chars[0]

        if isinstance(target, (dict, UserDict)):
            for i, (key, value) in enumerate(target.items()):
                if i > 0:
                    buff += ", "

                buff += indent_str + highlight_python(f"{key!r}: ")

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
            for i, value in enumerate(target):
                if i > 0:
                    buff += ", "

                pretty = prettify(
                    value,
                    indent=indent,
                    expand_all=expand_all,
                    force_markup=force_markup,
                    parse=False,
                )

                lines = pretty.splitlines()

                for line in lines:
                    buff += indent_str + line

        if indent > 0:
            buff += "\n"

        buff += chars[1]

        if force_markup:
            return buff

        return tim.parse(buff)

    if supports_fancy_repr(target):
        buff = build_fancy_repr(target)

    else:
        buff = highlight_python(str(target))

    return tim.parse(buff) if parse else buff
