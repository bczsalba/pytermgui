"""Classes to wrap anything that needs a border."""

from __future__ import annotations

from functools import cached_property
from typing import Type

from ..regex import real_length
from .base import Widget
from .styles import StyleManager

__all__ = [
    "Frame",
    "ASCII",
    "ASCII_X",
    "ASCII_O",
    "Light",
    "Heavy",
    "Double",
    "Rounded",
    "Frameless",
    "Padded",
]


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

    styles = StyleManager(
        border="surface",
        corner="surface2+2",
    )

    def __init__(self, parent: Widget) -> None:
        """Initializes Frame."""

        self._parent = parent
        self.styles = self.styles.branch(self._parent)

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

    @staticmethod
    def from_name(name: str) -> Type[Frame]:
        """Gets a builtin Frame type from its name."""

        if frame := globals().get(name):
            return frame

        raise ValueError(f"No frame defined with name {name!r}.")

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
        # width, height = self._parent.size
        width, height = self._parent.width, self._parent.height

        lines = lines[scroll.vertical : scroll.vertical + height]

        left_top, right_top, right_bottom, left_bottom = [
            self.styles.corner(corner) for corner in self.corners
        ]

        borders = [self.styles.border(char) for char in self.borders]

        top = (
            left_top
            + (width - real_length(left_top + right_top)) * borders[1]
            + right_top
        )

        bottom = (
            left_bottom
            + (width - real_length(left_bottom + right_bottom)) * borders[3]
            + right_bottom
        )

        framed = []

        if top != "":
            framed.append(top)

        for line in lines:
            # TODO: Implement horizontal scrolling
            framed.append(borders[0] + line + borders[2])

        if bottom != "":
            framed.append(bottom)

        return framed


class ASCII(Frame):
    """A frame made up of only ASCII characters.

    Preview:

    ```
    -----
    | x |
    -----
    ```
    """

    descriptor = [
        "-----",
        "| x |",
        "-----",
    ]


class ASCII_X(Frame):  # pylint: disable=invalid-name
    """A frame made up of only ASCII characters, with X-s in the corners.

    Preview:

    ```
    x---x
    | # |
    x---x
    ```
    """

    content_char = "#"

    descriptor = [
        "x---x",
        "| # |",
        "x---x",
    ]


class ASCII_O(Frame):  # pylint: disable=invalid-name
    """A frame made up of only ASCII characters, with X-s in the corners.

    Preview:

    ```
    o---o
    | x |
    o---o
    ```
    """

    content_char = "x"

    descriptor = [
        "o---o",
        "| x |",
        "o---o",
    ]


class Light(Frame):
    """A frame with a light outline.

    Preview:

    ```
    ┌───┐
    │ x │
    └───┘
    ```
    """

    descriptor = [
        "┌───┐",
        "│ x │",
        "└───┘",
    ]


class Heavy(Frame):
    """A frame with a heavy outline.

    Preview:

    ```
    ┏━━━┓
    ┃ x ┃
    ┗━━━┛
    ```
    """

    descriptor = [
        "┏━━━┓",
        "┃ x ┃",
        "┗━━━┛",
    ]


class Double(Frame):
    """A frame with a double outline.

    Preview:

    ```
    ╔═══╗
    ║ x ║
    ╚═══╝
    ```
    """

    descriptor = [
        "╔═══╗",
        "║ x ║",
        "╚═══╝",
    ]


class Rounded(Frame):
    """A frame with a light outline and rounded corners.

    Preview:

    ```
    ╭───╮
    │ x │
    ╰───╯
    ```
    """

    descriptor = [
        "╭───╮",
        "│ x │",
        "╰───╯",
    ]


class Frameless(Frame):
    """A frame that is not. No frame will be drawn around the object.

    Preview:

    ```

    x

    ```
    """

    descriptor = [
        "",
        "x",
        "",
    ]


class Padded(Frame):
    """A frame that pads its content by a single space on all sides.

    Preview:

    ```
    x
    ```
    """

    descriptor = [
        "   ",
        " x ",
        "   ",
    ]
