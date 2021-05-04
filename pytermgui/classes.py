"""
pytermgui.classes
-----------------
author: bczsalba


This module provides the classes used by the module.
"""

from __future__ import annotations
from typing import Optional, Callable, Union

from .exceptions import ElementError


class BaseElement:
    """ The element from which all UI classes derive from """

    def __init__(self, width: int = 0, pos: Optional[tuple[int, int]] = None) -> None:
        """ Initialize universal data for objects """

        self.width = width
        self.height = 1

        if pos is None:
            pos = 0, 0
        self.pos = pos

        self.forced_width: Optional[int] = None
        self.forced_height: Optional[int] = None

        self.depth = 0
        self.is_selectable = True

    def set_style(self, key: str, value: Union[Callable[[int, str], str], str]) -> None:
        """Set self.{key}_style to value

        Note:
            Setting a style to a str will make it static.
        """

    @property
    def posx(self) -> int:
        """ Return x position of object """

        return self.pos[0]

    @property
    def posy(self) -> int:
        """ Return y position of object """

        return self.pos[1]

    def __repr__(self) -> str:
        """ Stub for __repr__ method """


class Container(BaseElement):
    """ The element that serves as the outer parent to all other elements """

    def __init__(self, width: int = 0) -> None:
        """ Initialize Container data """

        super().__init__(width)
        self._elements: list[BaseElement] = []

    def __repr__(self) -> str:
        """ Return self._get_value() """

        return self._get_value()

    def __iadd__(self, other: object) -> Optional[Container]:
        """ Call self._add_element(other) and return self """

        if not isinstance(other, BaseElement):
            raise NotImplementedError(
                "You can only add BaseElements to other BaseElements."
            )

        self._add_element(other)
        return self

    def __add__(self, other: object) -> None:
        """ Call self._add_element(other) """

        self.__iadd__(other)

    def _get_value(self) -> str:
        """Get string value of object
        Note:
            Value could start off as the top border of the object,
            and every object could add left-right borders around it.
        """

        maxwidth = 0
        value = ""

        for element in self._elements:
            value += repr(element)
            maxwidth = max(element.width, maxwidth)

            if element.width is None:
                raise ElementError("Element width cannot be None.")

            if self.width is None:
                self.width = element.width

            if self.forced_width is not None and element.width > self.width:
                self.width = element.width

        if self.width == 0:
            self.width = maxwidth

        return value

    def _add_element(self, other: BaseElement) -> None:
        """ Add other to self._elements """

        self._elements.append(other)

        if other.forced_width is None:
            if self.forced_width is not None and other.width > self.width:
                self.width = other.width
            else:
                other.width = self.width

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
