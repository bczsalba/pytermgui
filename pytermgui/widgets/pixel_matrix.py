"""
The module containing all the widgets that can be used to display
pixel-based data.
"""

from __future__ import annotations

from .base import Widget
from ..parser import markup
from ..ansi_interface import MouseEvent, MouseAction


class PixelMatrix(Widget):
    """A matrix of pixels.

    The way this object should be used is by accessing & modifying
    the underlying matrix. This can be done using the set & getitem
    syntacies:

    ```python3
    from pytermgui import PixelMatrix

    matrix = PixelMatrix(10, 10, default="white")
    for y in matrix.rows:
        for x in matrix.columns:
            matrix[y, x] = "black"
    ```

    The above snippet draws a black diagonal going from the top left
    to bottom right.

    Each item of the rows should be a single PyTermGUI-parsable color
    string. For more information about this, see
    `pytermgui.ansi_interface.Color`.
    """

    def __init__(self, width: int, height: int, default: str = "", **attrs) -> None:
        """Initializes a PixelMatrix.

        Args:
            width: The amount of columns the matrix will have.
            height: The amount of rows the matrix will have.
            default: The default color to use to initialize the matrix with.
        """

        super().__init__(**attrs)

        self.static_width = width
        self.height = height

        self.rows = height
        self.columns = width

        self._matrix = []

        for _ in range(self.rows):
            self._matrix.append([default] * self.columns)

    @classmethod
    def from_matrix(cls, matrix: list[list[str]]) -> PixelMatrix:
        """Creates a PixelMatrix from the given matrix.

        Args:
            matrix: The matrix to use. This is a list of lists of strings
                with each element representing a PyTermGUI-parseable color.

        Returns:
            A new type(self).
        """

        obj = cls(len(matrix), max(len(row) for row in matrix))
        setattr(obj, "_matrix", matrix)

        return obj

    def get_lines(self) -> list[str]:
        """Gets PixelMatrix lines.

        The way the "half-resolution" look is achieved is by using unicode
        half-block characters, setting a foreground and background color
        for each.
        """

        lines = []
        lines_to_zip: list[list[str]] = []
        for row in self._matrix:
            lines_to_zip.append(row)
            if len(lines_to_zip) != 2:
                continue

            line = ""
            top_row, bottom_row = lines_to_zip[0], lines_to_zip[1]
            for bottom, top in zip(bottom_row, top_row):
                if len(top) + len(bottom) == 0:
                    line += " "
                    continue

                if bottom == "":
                    line += markup.parse(f"[{top}]▀")
                    continue

                markup_str = "@" + top + " " if len(top) > 0 else ""

                markup_str += bottom
                line += markup.parse(f"[{markup_str}]▄")

            lines.append(line)
            lines_to_zip = []

        return lines

    def __getitem__(self, indices: tuple[int, int]) -> str:
        """Gets a matrix item."""

        posy, posx = indices
        return self._matrix[posy][posx]

    def __setitem__(self, indices: tuple[int, int], value: str) -> None:
        """Sets a matrix item."""

        posy, posx = indices
        self._matrix[posy][posx] = value


class LargePixelMatrix(PixelMatrix):
    """A larger-scale pixel matrix.

    The factor of magnification going from normal PixelMatrix
    to this is about 4: While 1 pixel in PixelMatrix is displayed
    as a half-block, it is displayed as a cluster of 2 full blocks
    here.

    For more information, see `PixelMatrix`.

    Attributes:
        - selected_pixel: A tuple of the position & value (color) of the
            currently hovered pixel.
    """

    def __init__(self, width: int, height: int, default: str = "", **attrs) -> None:
        """Initializes LargePixelMatrix.

        Args:
            width: The width of the matrix.
            height: The height of the matrix.
            default: The default color to use to initialize the matrix with.

        Note:
            The `column` attribute is faithful to the matrix dimensions,
            while the width follows the scaling applied by being set
            to double the column value.
        """

        super().__init__(width, height, default, **attrs)

        self.rows = height
        self.columns = width

        self.width = width * 2
        self.selected_pixel: tuple[tuple[int, int], str] | None = None

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handles a mouse event.

        On hover, the `selected_pixel` attribute is set to the current pixel.
        """

        if event.action is MouseAction.HOVER:
            xoffset = event.position[0] - self.pos[0]
            yoffset = event.position[1] - self.pos[1]

            color = self._matrix[yoffset][xoffset // 2]

            self.selected_pixel = ((yoffset, xoffset), color)
            return True

        return False

    def get_lines(self) -> list[str]:
        """Gets large pixel matrix lines."""

        lines = []
        for row in self._matrix:
            line = ""
            for pixel in row:
                if len(pixel) > 0:
                    line += f"[@{pixel}]  "
                else:
                    line += "[/]  "

            lines.append(markup.parse(line))

        return lines
