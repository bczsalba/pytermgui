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

    # left, top, right, bottom
    borders: tuple[str, str, str, str]

    # left_top, right_top, right_bottom, left_bottom
    corners: tuple[str, str, str, str]

    def __init__(self, parent: Widget) -> None:
        """Initializes Frame."""

        self._parent = parent

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

        scroll = self._parent.scroll

        # TODO: Widget.size should substract frame size, once
        #       it is aware of the frame.
        _, height = self._parent.size

        lines = lines[scroll.vertical : scroll.vertical + height]

        left, top, right, bottom = self.borders
        left_top, right_top, right_bottom, left_bottom = self.corners

        top = (
            left_top
            + (self._parent.width - real_length(left_top + right_top)) * top
            + right_top
        )

        bottom = (
            left_bottom
            + (self._parent.width - real_length(left_bottom + right_bottom)) * bottom
            + right_bottom
        )

        framed = [top]
        for line in lines:
            # TODO: Implement horizontal scrolling
            framed.append(left + line + right)

        return framed + [bottom]


class Single(Frame):
    """A frame with a single, square border.

    ```
    ┌───┐
    │ x │
    └───┘
    ```
    """

    borders = ["│", "─", "│", "─"]
    corners = ["┌", "┐", "┘", "└"]
