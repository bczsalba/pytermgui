"""
The module containing all the widgets that can be used to display
pixel-based data.
"""

from __future__ import annotations

from ..ansi_interface import MouseEvent
from ..markup import tim
from ..regex import real_length
from .base import Widget

__all__ = [
    "PixelMatrix",
    "DensePixelMatrix",
]


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

    selected_pixel: tuple[tuple[int, int], str] | None
    """A tuple of the position & value (color) of the currently hovered pixel."""

    def __init__(
        self, width: int, height: int, default: str = "background", **attrs
    ) -> None:
        """Initializes a PixelMatrix.

        Args:
            width: The amount of columns the matrix will have.
            height: The amount of rows the matrix will have.
            default: The default color to use to initialize the matrix with.
        """

        super().__init__(**attrs)

        self.rows = height
        self.columns = width

        self._matrix = []

        for _ in range(self.rows):
            self._matrix.append([default] * self.columns)

        self.selected_pixel = None
        self.build()

    @classmethod
    def from_matrix(cls, matrix: list[list[str]]) -> PixelMatrix:
        """Creates a PixelMatrix from the given matrix.

        The given matrix should be a list of rows, each containing a number
        of cells. It is optimal for all rows to share the same amount of cells.

        Args:
            matrix: The matrix to use. This is a list of lists of strings
                with each element representing a PyTermGUI-parseable color.

        Returns:
            A new type(self).
        """

        obj = cls(max(len(row) for row in matrix), len(matrix))
        setattr(obj, "_matrix", matrix)
        obj.build()

        return obj

    def _update_dimensions(self, lines: list[str]):
        """Updates the dimensions of this matrix.

        Args:
            lines: A list of lines that the calculations will be based upon.
        """

        self.static_width = max(real_length(line) for line in lines)
        self.height = len(lines)

    def on_hover(self, event: MouseEvent) -> bool:
        """Sets `selected_pixel` to the current pixel."""

        xoffset = event.position[0] - self.pos[0]
        yoffset = event.position[1] - self.pos[1]

        color = self._matrix[yoffset][xoffset // 2]

        self.selected_pixel = ((xoffset // 2, yoffset), color)
        return True

    def get_lines(self) -> list[str]:
        """Returns lines built by the `build` method."""

        return self._lines

    def build(self) -> list[str]:
        """Builds the image pixels.

        Returns:
            The lines that this object will return, until a subsequent `build` call.
            These lines are stored in the `self._lines` variable.
        """

        lines: list[str] = []
        for row in self._matrix:
            line = ""
            for pixel in row:
                if len(pixel) > 0 and pixel != "background":
                    line += f"[@{pixel}]  "
                else:
                    line += "[/ background]  "

            lines.append(tim.parse(line))

        self._lines = lines
        self._update_dimensions(lines)

        return lines

    def __getitem__(self, indices: tuple[int, int]) -> str:
        """Gets a matrix item."""

        posy, posx = indices
        return self._matrix[posy][posx]

    def __setitem__(self, indices: tuple[int, int], value: str) -> None:
        """Sets a matrix item."""

        posy, posx = indices
        self._matrix[posy][posx] = value


class DensePixelMatrix(PixelMatrix):
    """A more dense (2x) PixelMatrix.

    Due to each pixel only occupying 1/2 characters in height, accurately
    determining selected_pixel is impossible, thus the functionality does
    not exist here.
    """

    def __init__(self, width: int, height: int, default: str = "", **attrs) -> None:
        """Initializes DensePixelMatrix.

        Args:
            width: The width of the matrix.
            height: The height of the matrix.
            default: The default color to use to initialize the matrix with.
        """

        super().__init__(width, height, default, **attrs)

        self.width = width // 2

    def handle_mouse(self, event: MouseEvent) -> bool:
        """As mentioned in the class documentation, mouse handling is disabled here."""

        return False

    def build(self) -> list[str]:
        """Builds the image pixels, using half-block characters.

        Returns:
            The lines that this object will return, until a subsequent `build` call.
            These lines are stored in the `self._lines` variable.
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
                    line += tim.parse(f"[{top}]▀")
                    continue

                markup_str = "@" + top + " " if len(top) > 0 else ""

                markup_str += bottom
                line += tim.parse(f"[{markup_str}]▄")

            lines.append(line)
            lines_to_zip = []

        self._lines = lines
        self._update_dimensions(lines)

        return lines
