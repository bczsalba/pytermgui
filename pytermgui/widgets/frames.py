"""Classes to wrap anything that needs a border."""

from __future__ import annotations

from functools import cached_property

from ..regex import real_length
from .base import Widget

__all__ = ["Frame", "Single"]


class Frame:
    """An object that wraps a frame around its parent.

    It can be used by any widget in order to draw a 'box' around itself. It
    implements scrolling as well.
    """

    descriptor: str
    content_char: str = "x"

    # left, top, right, bottom
    borders: tuple[str, str, str, str]

    # left_top, right_top, right_bottom, left_bottom
    corners: tuple[str, str, str, str]

    def __init__(self, parent: Widget) -> None:
        """Initializes Frame."""

        self._parent = parent

        if self.descriptor is not None:
            self._init_from_descriptor()

    def _init_from_descriptor(self) -> None:
        """Initializes the Frame's border & corner chars from the content property."""

        top, _, bottom = self.descriptor
        top_left, top_right = self._get_corners(top)
        bottom_left, bottom_right = self._get_corners(bottom)

        self.borders = list(self._get_borders(self.descriptor))
        self.corners = [
            top_left,
            top_right,
            bottom_right,
            bottom_left,
        ]

    @staticmethod
    def _find_mode_char(line: str) -> str:
        """Finds the most often consecutively occuring character."""

        instances = 0
        current_char = ""

        results: list[tuple[str, int]] = []
        for char in line:
            if current_char == char:
                instances += 1
            else:
                if len(current_char) > 0:
                    results.append((current_char, instances))

                instances = 1
                current_char = char

        results.append((current_char, instances))

        results.sort(key=lambda item: item[1])
        if len(results) == 0:
            print(line, instances, current_char)

        return results[-1][0]

    def _get_corners(self, line: str) -> tuple[str, str]:
        """Gets corners from a line."""

        mode_char = self._find_mode_char(line)
        left = line[: line.index(mode_char)]
        right = line[real_length(line) - (line[::-1].index(mode_char)) :]

        return left, right

    def _get_borders(self, lines: list[str]) -> tuple[str, str, str, str]:
        """Gets borders from all lines."""

        top, middle, bottom = lines
        middle_reversed = middle[::-1]

        top_border = self._find_mode_char(top)
        left_border = middle[: middle.index(self.content_char)]

        right_border = middle[
            real_length(middle) - middle_reversed.index(self.content_char) :
        ]
        bottom_border = self._find_mode_char(bottom)

        return left_border, top_border, right_border, bottom_border

    @cached_property
    def left_size(self) -> int:
        """Returns the length of the left border character."""

        return real_length(self.borders[0])

    @cached_property
    def top_size(self) -> int:
        """Returns the height of the top border."""

        return 1

    @cached_property
    def right_size(self) -> int:
        """Returns the length of the right border character."""

        return real_length(self.borders[2])

    @cached_property
    def bottom_size(self) -> int:
        """Returns the height of the bottom border."""

        return 1

    def __call__(self, lines: list[str]) -> list[str]:
        """Frames the given lines, handles scrolling when necessary.

        Args:
            lines: A list of lines to 'frame'. If there are too many
                lines, they are clipped according to the parent's
                `scroll` field.

        Returns:
            Framed lines, clipped to the current scrolling settings.
        """

        if len(self.borders) != 4 or len(self.corners) != 4:
            raise ValueError("Cannot frame with no border or corner values.")

        scroll = self._parent.scroll

        # TODO: Widget.size should substract frame size, once
        #       it is aware of the frame.
        _, height = self._parent.size

        lines = lines[scroll.vertical : scroll.vertical + height]

        left_top, right_top, right_bottom, left_bottom = self.corners

        top = (
            left_top
            + (self._parent.width - real_length(left_top + right_top)) * self.borders[1]
            + right_top
        )

        bottom = (
            left_bottom
            + (self._parent.width - real_length(left_bottom + right_bottom))
            * self.borders[3]
            + right_bottom
        )

        framed = [top]
        for line in lines:
            # TODO: Implement horizontal scrolling
            framed.append(self.borders[0] + line + self.borders[2])

        return framed + [bottom]


class Single(Frame):
    """A frame with a single, square border."""

    descriptor = [
        "┌───┐",
        "│ x │",
        "└───┘",
    ]
