"""The module containing the ColorPicker widget, as well as some helpers it needs.

To test out the widget, run `ptg --color`!
"""

from __future__ import annotations

from typing import Any
from contextlib import suppress

from . import boxes
from .layouts import Container
from .base import Label, Widget
from .interactive import Button
from ..animations import animator
from ..helpers import real_length
from .pixel_matrix import PixelMatrix
from ..enums import SizePolicy, HorizontalAlignment
from ..ansi_interface import MouseAction, MouseEvent


def _get_xterm_matrix() -> list[list[str]]:
    """Creates a matrix containing all 255 xterm-255 colors.

    The top row contains the normal & bright colors, with some
    space in between.

    The second row contains all shades of black.

    Finally, the third section is a table of all remaining colors.
    """

    matrix: list[list[str]] = []
    for _ in range(11):
        current_row = []
        for _ in range(36):
            current_row.append("")
        matrix.append(current_row)

    offset = 0
    for color in range(16):
        if color == 8:
            offset += 4

        cursor = offset
        for _ in range(2):
            matrix[0][cursor] = str(color)
            cursor += 1

        offset = cursor

    offset = 7
    for color in range(23):
        cursor = offset

        matrix[2][cursor] = str(232 + color)
        matrix[3][cursor] = str(min(232 + color + 1, 255))
        cursor += 1

        offset = cursor

    cursor = 16
    for row in range(5, 11):
        for column in range(37):
            if column == 36:
                continue

            matrix[row][column] = str(cursor + column)

        cursor += column

        if cursor > 232:
            break

    return matrix


class Joiner(Container):
    """A Container that stacks widgets horizontally, without filling up the available space.

    This works slightly differently to Splitter, as that applies padding & custom widths to
    any Widget it finds. This works much more simply, and only joins their lines together as
    they come.
    """

    parent_align = HorizontalAlignment.LEFT

    chars = {"separator": " "}

    def get_lines(self) -> list[str]:
        """Does magic"""

        lines: list[str] = []
        separator = self._get_char("separator")
        assert isinstance(separator, str)

        line = ""
        for widget in self._widgets:
            if len(line) > 0:
                line += separator

            widget.pos = (self.pos[0] + real_length(line), self.pos[1] + len(lines))
            widget_line = widget.get_lines()[0]

            if real_length(line + widget_line) >= self.width:
                lines.append(line)
                widget.pos = self.pos[0], self.pos[1] + len(lines)
                line = widget_line
                continue

            line += widget_line

        lines.append(line)
        self.height = len(lines)
        return lines


class _FadeInButton(Button):
    """A Button with a fade-in animation."""

    def __init__(self, *args: Any, **attrs: Any) -> None:
        """Initialize _FadeInButton.

        As this is nothing more than an extension on top of
        `pytermgui.widgets.interactive.Button`, check that documentation
        for more informationA.
        """

        super().__init__(*args, **attrs)
        self.onclick = self.remove_from_parent
        self.set_char("delimiter", ["", ""])

        self.set_style("label", lambda _, item: item)
        self._fade_progress = 0

        self.get_lines()
        animator.animate(
            self, "_fade_progress", startpoint=0, endpoint=self.width, duration=150
        )

    def remove_from_parent(self, _: Widget) -> None:
        """Removes self from parent, when possible."""

        def _on_finish(self) -> None:
            """Removes button on animation finish."""

            with suppress(ValueError):
                self.parent.remove(self)

        animator.animate(
            self,
            "_fade_progress",
            startpoint=self.width,
            endpoint=0,
            duration=150,
            finish_callback=_on_finish,
        )

    def get_lines(self) -> list[str]:
        """Gets the lines from Button, and cuts them off at self._fade_progress"""

        lines = super().get_lines()
        for i, line in enumerate(lines):
            lines[i] = line[: self._fade_progress].rstrip("\x1b") + "\x1b[0m"
        return lines


class ColorPicker(Container):
    """A simple ColorPicker widget.

    This is used to visualize xterm-255 colors. RGB colors are not
    included here, as it is probably easier to use a web-based picker
    for those anyways.
    """

    size_policy = SizePolicy.STATIC

    def __init__(self, show_output: bool = True, **attrs: Any) -> None:
        """Initializes a ColorPicker.

        Attrs:
            show_output: Decides whether the output Container should be
                added. If not set, the widget will only display the
                PixelMatrix of colors.
        """

        super().__init__(**attrs)
        self.show_output = show_output

        self._matrix = PixelMatrix.from_matrix(_get_xterm_matrix())

        self.width = 72
        self.box = boxes.EMPTY

        self._add_widget(self._matrix, run_get_lines=False)

        self.chosen = Joiner()
        self._output = Container(self.chosen, "", "", "")
        self._output.height = 7
        self._output.box = boxes.Box([" ", "x", " "])

        if self.show_output:
            self._add_widget(self._output)

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handles mouse events.

        On hover, the widget will display the currently hovered
        color and some testing text.

        On click, it will add a _FadeInButton for the currently
        hovered color.

        Args:
            event: The event to handle.
        """

        if super().handle_mouse(event):
            return True

        if not self.show_output or not self._matrix.contains(event.position):
            return False

        if event.action is MouseAction.LEFT_CLICK:
            if self._matrix.selected_pixel is None:
                return True

            _, color = self._matrix.selected_pixel
            if len(color) == 0:
                return False

            # Why does mypy freak out about this?
            self.chosen += _FadeInButton(f"[black @{color}]{color:^5}")  # type: ignore
            return True

        return False

    def get_lines(self) -> list[str]:
        """Updates self._output and gets widget lines."""

        if self.show_output and self._matrix.selected_pixel is not None:
            _, color = self._matrix.selected_pixel
            if len(color) == 0:
                return super().get_lines()

            lines: list[Widget] = [
                Label(f"[black @{color}] {color} [/ {color}] {color}"),
                Label(
                    f"[{color} bold]Here[/bold italic] is "
                    + "[/italic underline]some[/underline dim] example[/dim] text"
                ),
            ]
            self._output.set_widgets(lines + [Label(), self.chosen])
            return super().get_lines()

        return super().get_lines()
