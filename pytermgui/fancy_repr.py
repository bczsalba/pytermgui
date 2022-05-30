"""The `__fancy_repl__` protocol."""

from __future__ import annotations

from typing import Dict, Generator, Protocol, Union

from .highlighters import highlight_python

FancyYield = Union[str, Dict[str, Union[str, bool]]]

__all__ = [
    "SupportsFancyRepr",
    "supports_fancy_repr",
    "build_fancy_repr",
]


class SupportsFancyRepr(Protocol):  # pylint: disable=too-few-public-methods
    """An object that supports the `__fancy_repr__` dunder."""

    def __fancy_repr__(self) -> Generator[FancyYield, None, None]:
        """Yields some fancy text.

        Each value yielded can be one of two types. If a dictionary is yielded,
        it will be assumed to have `text` and `highlight` fields. `text` will be
        the string included in the repr, and `highlight` will be a boolean describing
        whether the part should be highlighted. At the moment highlighting is done by
        `highlight_python`, but this might be configurable once more highlighters are
        available.

        If a `str` is yielded, it is assumed to be a shorthand for:

            {"text": <your_text>, "highlight": True}
        """


def supports_fancy_repr(obj: object) -> bool:
    """Determines whether the given object supports the fancy repl protocol."""

    return hasattr(obj, "__fancy_repr__") and not isinstance(obj, type)


def build_fancy_repr(obj: SupportsFancyRepr) -> str:
    """Interprets objects with the `__fancy_repr__` protocol."""

    output = ""
    for item in obj.__fancy_repr__():
        if isinstance(item, str):
            output += highlight_python(item)
            continue

        text = item["text"]
        assert isinstance(text, str)

        highlight = item["highlight"]

        if highlight:
            text = highlight_python(text)

        output += text

    return output
