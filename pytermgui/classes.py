"""
pytermgui.classes
-----------------
author: bczsalba


This module provides the classes used by the module.
"""

from __future__ import annotations
from typing import Optional, Callable, Union

from .helpers import real_length
from .exceptions import ElementError
from .context_managers import cursor_at


StyleType = Union[Callable[[int, str], str], str]


def not_implemented_style(depth: int, item: str) -> str:
    """A style callable that hasn't been implemented"""

    _ = depth
    return item


class BaseElement:
    """The element from which all UI classes derive from"""

    # it makes sense to have this many.
    # pylint: disable=too-many-instance-attributes
    def __init__(self, width: int = 0, pos: Optional[tuple[int, int]] = None) -> None:
        """Initialize universal data for objects"""

        self.width = width
        self.height = 1

        if pos is None:
            pos = 1, 1
        self.pos = pos

        self.forced_width: Optional[int] = None
        self.forced_height: Optional[int] = None

        self.depth = 0
        self.styles: dict[str, StyleType] = {}
        self.chars: dict[str, list[str]] = {}
        self.is_selectable = True

    def set_style(self, key: str, value: StyleType) -> None:
        """Set self.{key}_style to value"""

        key += "_style"
        if not key in self.styles.keys():
            raise KeyError(f"Style {key} is not valid for {type(self)}!")

        self.styles[key] = value

    def set_char(self, key: str, value: list[str]) -> None:
        """Set self.{key}_char to value"""

        key += "_char"
        if not key in self.chars.keys():
            raise KeyError(f"Char {key} is not valid for {type(self)}!")

        self.chars[key] = value

    def get_lines(self) -> list[str]:
        """Stub for element.get_lines"""

        return [type(self).__name__]

    @property
    def posx(self) -> int:
        """Return x position of object"""

        return self.pos[0]

    @property
    def posy(self) -> int:
        """Return y position of object"""

        return self.pos[1]

    def __repr__(self) -> str:
        """Stub for __repr__ method"""


class Container(BaseElement):
    """The element that serves as the outer parent to all other elements"""

    def __init__(self, width: int = 0) -> None:
        """Initialize Container data"""

        super().__init__(width)
        self._elements: list[BaseElement] = []

        self.styles = {
            "border": not_implemented_style,
        }

        self.chars = {
            "border": ["| ", "-", " |", "-"],
            "corner": [""] * 4,
        }

    @property
    def sidelength(self) -> int:
        """Returns length of left+right borders"""

        left_border, _, right_border, _ = self.chars["border"]
        return real_length(left_border + right_border)

    def __repr__(self) -> str:
        """Return self.get_lines()"""

        posx, posy = self.pos

        out = ""
        for i, line in enumerate(self.get_lines()):
            out += f"\033[{posy+i};{posx}H" + line

        return out

    def __iadd__(self, other: object) -> Optional[Container]:
        """Call self._add_element(other) and return self"""

        if not isinstance(other, BaseElement):
            raise NotImplementedError(
                "You can only add BaseElements to other BaseElements."
            )

        self._add_element(other)
        return self

    def __add__(self, other: object) -> None:
        """Call self._add_element(other)"""

        self.__iadd__(other)

    def _add_element(self, other: BaseElement) -> None:
        """Add other to self._elements"""

        self._elements.append(other)
        other.depth = self.depth + 1
        other.get_lines()

        if other.forced_width is None and self.forced_width is None:
            if other.width is not None and other.width >= self.width:
                self.width = other.width + self.sidelength
            else:
                other.width = self.width - self.sidelength

        else:
            if self.forced_width is not None:
                if (
                    other.forced_width is not None
                    and self.forced_width < other.forced_width
                ):
                    raise ElementError(
                        "Added element's forced_width is higher than the on it is being added to."
                    )

                self.width = other.width

        self.height += other.height

    def get_lines(self) -> list[str]:
        """Get lines to represent the object"""

        def _apply_forced_width(source: BaseElement, target: BaseElement) -> bool:
            """Apply source's forced_width attribute to target, return False if not possible."""

            if source.forced_width is not None and target.forced_width is None:
                source.width = source.forced_width
                if source.width > target.width - self.sidelength:
                    target.width = source.width + self.sidelength
                return True

            return False

        lines = []
        left_border, top_border, right_border, bottom_border = self.chars["border"]

        for element in self._elements:
            if not _apply_forced_width(element, self):
                _apply_forced_width(self, element)

            # this is needed because of unknown reasons :(
            container_offset = 1 if not isinstance(element, Container) else 0

            if element.width >= self.width:
                self.width = element.width + self.sidelength + container_offset
            else:
                element.width = self.width - self.sidelength - container_offset

            lines += [left_border + line + right_border for line in element.get_lines()]

        lines.insert(0, self.width * top_border)
        lines.append(self.width * bottom_border)
        return lines

    def print(self) -> None:
        """Print object"""

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(line)


class Label(BaseElement):
    """Unselectable text object"""

    ALIGN_LEFT = 0
    ALIGN_CENTER = 1
    ALIGN_RIGHT = 2

    def __init__(self, value: str = "", align: int = ALIGN_CENTER) -> None:
        """Set up object"""

        super().__init__()

        self.value = value
        self.align = align
        self.padding = 0
        self.width = len(value) + self.padding

        self.styles = {
            "value": not_implemented_style,
        }

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        value_style = self.styles["value"]

        if self.align is Label.ALIGN_CENTER:
            padding = (self.width - real_length(self.value) - self.padding) // 2
            outline = (padding + self.padding + 1) * " " + self.value
            outline += (self.width - real_length(outline) + 1) * " "

            lines = [outline]

        elif self.align is Label.ALIGN_LEFT:
            padding = self.width - real_length(self.value) - self.padding + 1
            lines = [self.padding * " " + self.value + padding * " "]

        elif self.align is Label.ALIGN_RIGHT:
            lines = [
                (self.width - real_length(self.value) - self.padding + 1) * " "
                + self.value
                + self.padding * " "
            ]

        return [value_style(self.depth, line) for line in lines]
