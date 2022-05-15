"""This module provides introspection utilities.

The `inspect` method can be used to create an `Inspector` widget, which can
then be used to see what is happening inside any python object. This method is
usually preferred for instantiating an `Inspector`, as it sets up overwriteable default
arguments passed to the new widget.

These defaults are meant to hide the non-important information when they are not needed,
in order to allow the least amount of code for the most usability. For example, by
default, when passed a class, `inspect` will clip the docstrings to their first lines,
but show all methods. When an class' method is given it will hide show the full
docstring, and also use the method's fully qualified name.
"""

# pylint: disable=too-many-instance-attributes

# Note: There are a lot of `type: ignore`-s in this file. These show up in places where
#       mypy sees potential for an error, but the possible error is already counteracted.

from __future__ import annotations

from enum import Enum, auto as _auto
from typing import Any

from inspect import (
    signature,
    isclass,
    ismodule,
    isfunction,
    isbuiltin,
    getdoc,
    getfile,
)

from .parser import tim
from .terminal import terminal
from .prettifiers import prettify
from .highlighters import highlight_python
from .regex import real_length, RE_MARKUP
from .widgets import Widget, Container, Label, boxes

try:
    from typing import get_origin  # pylint: disable=ungrouped-imports

except NameError:

    def get_origin(_: object) -> Any:  # type: ignore
        """Spoofs typing.get_origin, which is used to determine type-hints.

        Since this function is only available >=3.8, we need to have some
        implementation on it for 3.7. The code checks for the origin to be
        non-null, as that is the value returned by this method on non-typing
        objects.

        This will cause annotations to show up on 3.7, but not on 3.8+.
        """

        return None


__all__ = ["Inspector", "inspect"]


class ObjectType(Enum):
    """All types an object can be."""

    LIVE = _auto()
    """An instance that does not fit the other types."""

    CLASS = _auto()
    """A class object."""

    MODULE = _auto()
    """A module object."""

    BUILTIN = _auto()
    """Some sort of a builtin object.

    As builtins are often implemented in C, a lot of the standard python APIs
    won't work on them, so we need to treat them separately."""

    FUNCTION = _auto()
    """A callable object, that is not a class."""


def _is_builtin(target: object) -> bool:
    """Determines if the given target is a builtin."""

    try:
        signature(target)  # type: ignore
        return False

    except (ValueError, TypeError):
        return True


def _determine_type(target: object) -> ObjectType:
    """Determines the type of an object."""

    if ismodule(target):
        return ObjectType.MODULE

    if _is_builtin(target):
        return ObjectType.BUILTIN

    if isclass(target):
        return ObjectType.CLASS

    if isfunction(target) or callable(target):
        return ObjectType.FUNCTION

    return ObjectType.LIVE


def _is_type_alias(obj: object) -> bool:
    """Determines whether the given object is (likely) a type alias."""

    return get_origin(obj) is not None


INDENTED_EMPTY_BOX = boxes.Box(
    [
        "   ",
        "   x",
        "",
    ]
)


def inspect(target: object, **inspector_args) -> Inspector:
    """Inspects an object.

    Args:
        obj: The object to inspect.
        show_private: Whether `_private` attributes should be shown.
        show_dunder: Whether `__dunder__` attributes should be shown.
        show_methods: Whether methods should be shown when encountering a class.
        show_full_doc: If not set, docstrings are cut to only include their first
            line.
        show_qualname: Show fully-qualified name, e.g. `module.submodule.name`
            instead of `name`.
    """

    def _conditionally_overwrite_kwarg(**kwargs) -> None:
        for key, value in kwargs.items():
            if inspector_args.get(key) is None:
                inspector_args[key] = value

    if ismodule(target):
        _conditionally_overwrite_kwarg(
            show_dunder=False,
            show_private=False,
            show_full_doc=False,
            show_methods=True,
            show_qualname=False,
        )

    elif isclass(target):
        _conditionally_overwrite_kwarg(
            show_dunder=False,
            show_private=False,
            show_full_doc=True,
            show_methods=True,
            show_qualname=False,
        )

    elif callable(target) or isbuiltin(target):
        _conditionally_overwrite_kwarg(
            show_dunder=False,
            show_private=False,
            show_full_doc=True,
            show_methods=False,
            show_qualname=True,
        )

    else:
        _conditionally_overwrite_kwarg(
            show_dunder=False,
            show_private=False,
            show_full_doc=True,
            show_methods=True,
            show_qualname=False,
        )

    inspector = Inspector(**inspector_args).inspect(target)

    return inspector


class Inspector(Container):
    """A widget to inspect any Python object."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        target: object = None,
        show_private: bool = False,
        show_dunder: bool = False,
        show_methods: bool = False,
        show_full_doc: bool = False,
        show_qualname: bool = True,
        **attrs: Any,
    ):
        """Initializes an inspector.

        Note that most of the time, using `inspect` to do this is going to be more
        useful.

        Some styles of the inspector can be changed using the `code.name`,
        `code.file` and `code.keyword` markup aliases. The rest of the
        highlighting is done using `pprint`, with all of its respective colors.

        Args:
            show_private: Whether `_private` attributes should be shown.
            show_dunder: Whether `__dunder__` attributes should be shown.
            show_methods: Whether methods should be shown when encountering a class.
            show_full_doc: If not set, docstrings are cut to only include their first
                line.
            show_qualname: Show fully-qualified name, e.g. `module.submodule.name`
                instead of `name`.
        """

        if "box" not in attrs:
            attrs["box"] = "EMPTY"

        super().__init__(**attrs)

        self.width = terminal.width
        self.show_private = show_private
        self.show_dunder = show_dunder
        self.show_methods = show_methods
        self.show_full_doc = show_full_doc
        self.show_qualname = show_qualname

        # TODO: Fix attr-showing
        self.show_attrs = False

        self.target: object
        if target is not None:
            self.inspect(target)
            self.target = target

    def _get_header(self) -> Container:
        """Creates a header containing the name and location of the object."""

        header = Container(box="SINGLE")

        line = "[code.name]"
        if self.target_type is ObjectType.MODULE:
            line += self.target.__name__  # type: ignore

        else:
            cls = (
                self.target
                if isclass(self.target) or isfunction(self.target)
                else self.target.__class__
            )
            line += cls.__module__ + "." + cls.__qualname__  # type: ignore

        header += line

        try:
            file = getfile(self.target)  # type: ignore
        except TypeError:
            return header

        header += f"Located in [code.file !link(file://{file})]{file}[/]"

        return header

    def _get_definition(self) -> Label:
        """Returns the definition str of self.target."""

        target = self.target

        if self.show_qualname:
            name = getattr(target, "__qualname__", type(target).__name__)
        else:
            name = getattr(target, "__name__", type(target).__name__)

        if self.target_type == ObjectType.LIVE:
            target = type(target)

        otype = _determine_type(target)

        keyword = ""
        if otype == ObjectType.CLASS:
            keyword = "class "

        elif otype == ObjectType.FUNCTION:
            keyword = "def "

        try:
            assert callable(target)
            definition = self.highlight(keyword + name + str(signature(target)) + ":")

        except (TypeError, ValueError, AssertionError):
            definition = self.highlight(keyword + name + "(...)")

        return Label(definition, parent_align=0, non_first_padding=4)

    def _get_docs(self, padding: int) -> Label:
        """Returns a list of Labels of the object's documentation."""

        default = Label("...", style="102")
        if self.target.__doc__ is None:
            return default

        doc = getdoc(self.target)

        if doc is None:
            return default

        lines = doc.splitlines()
        if not self.show_full_doc and len(lines) > 0:
            lines = [lines[0]]

        trimmed = "\n".join(lines)

        return Label(
            trimmed.replace("[", r"\["),
            style="102",
            parent_align=0,
            padding=padding,
        )

    def _get_keys(self) -> list[str]:
        """Gets all inspectable keys of an object.

        It first checks for an `__all__` attribute, and substitutes `dir` if not found.
        Then, if there are too many keys and the given target is a module it tries to
        list all of the present submodules.
        """

        keys = getattr(self.target, "__all__", dir(self.target))

        if not self.show_dunder:
            keys = [key for key in keys if not key.startswith("__")]

        if not self.show_private:
            keys = [key for key in keys if not (key.startswith("_") and key[1] != "_")]

        if not self.show_methods:
            keys = [
                key for key in keys if not callable(getattr(self.target, key, None))
            ]

        keys.sort(key=lambda item: callable(getattr(self.target, item, None)))

        return keys

    def _get_preview(self) -> Container:
        """Gets a Container with self.target inside."""

        preview = Container(static_width=self.width // 2, parent_align=0, box="SINGLE")

        if isinstance(self.target, str) and RE_MARKUP.match(self.target) is not None:
            preview += Label(prettify(self.target, parse=False), parent_align=0)
            return preview

        for line in prettify(self.target).splitlines():

            if real_length(line) > preview.width - preview.sidelength:
                preview.width = real_length(line) + preview.sidelength

            preview += Label("[str]" + tim.get_markup(line), parent_align=0)

        preview.width = min(preview.width, self.terminal.width - preview.sidelength)
        return preview

    @staticmethod
    def highlight(text: str) -> str:
        """Applies highlighting to a given string.

        This highlight includes keywords, builtin types and more.

        Args:
            text: The string to highlight.

        Returns:
            Unparsed markup.
        """

        def _split(text: str, chars: str = " ,:|()[]{}") -> list[tuple[str, str]]:
            """Splits given text by the given chars.

            Args:
                text: The text to split.
                chars: A string of characters we will split by.

            Returns:
                A tuple of (delimiter, word) tuples. Delimiter is one of the characters
                of `chars`.
            """

            last_delim = ""
            output = []
            word = ""
            for char in text:
                if char in chars:
                    output.append((last_delim, word))
                    last_delim = char
                    word = ""
                    continue

                word += char

            output.append((last_delim, word))
            return output

        buff = ""
        for (delim, word) in _split(text):
            stripped = word.strip("'")
            highlighted = highlight_python(stripped)

            if highlighted != stripped:
                buff += delim + stripped
                continue

            buff += delim + stripped

        return highlight_python(buff)

    def inspect(self, target: object) -> Inspector:
        """Inspects a given object, and sets self.target to it.

        Returns:
            Self, with the new content based on the inspection.
        """

        self.target = target
        self.target_type = _determine_type(target)

        # Header
        if self.box is not INDENTED_EMPTY_BOX:
            self.lazy_add(self._get_header())

        # Body
        if self.target_type is not ObjectType.MODULE:
            self.lazy_add(self._get_definition())

        padding = 0 if self.target_type is ObjectType.MODULE else 4

        self.lazy_add(self._get_docs(padding))

        keys = self._get_keys()

        for key in keys:
            attr = getattr(target, key, None)

            # Don't show type aliases
            if _is_type_alias(attr):
                continue

            # Only show functions if they are not lambdas
            if (isfunction(attr) or callable(attr)) and (
                hasattr(attr, "__name__") and not attr.__name__ == "<lambda>"
            ):
                self.lazy_add(
                    Inspector(
                        box=INDENTED_EMPTY_BOX,
                        show_dunder=self.show_dunder,
                        show_private=self.show_private,
                        show_full_doc=False,
                        show_qualname=self.show_qualname,
                    ).inspect(attr)
                )
                continue

            if not self.show_attrs:
                continue

            for i, line in enumerate(prettify(attr, parse=False).splitlines()):
                if i == 0:
                    line = f"- {key}: {line}"

                self.lazy_add(Label(line, parent_align=0))

        # Footer
        if self.target_type in [ObjectType.LIVE, ObjectType.BUILTIN]:
            self.lazy_add(self._get_preview())

        return self

    def debug(self) -> str:
        """Returns identifiable information used in repr."""

        if terminal.is_interactive and not terminal.displayhook_installed:
            return "\n".join(self.get_lines())

        return Widget.debug(self)
