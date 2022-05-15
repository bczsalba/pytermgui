"""The module containing the ColorPicker widget, as well as some helpers it needs.

To test out the widget, run `ptg --color`!
"""

from __future__ import annotations

from typing import Any
from contextlib import suppress

from . import boxes
from ..regex import real_length
from .base import Label, Widget
from .interactive import Button
from ..colors import str_to_color
from .containers import Container
from ..animations import animator
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
        for more information.
        """

        super().__init__(*args, **attrs)
        self.onclick = self.remove_from_parent
        self.set_char("delimiter", ["", ""])

        self._fade_progress = 0

        self.get_lines()

        # TODO: Why is that +2 needed?
        animator.animate_attr(
            target=self,
            attr="_fade_progress",
            start=0,
            end=self.width + 2,
            duration=150,
        )

    def remove_from_parent(self, _: Widget) -> None:
        """Removes self from parent, when possible."""

        def _on_finish(_: object) -> None:
            """Removes button on animation finish."""

            assert isinstance(self.parent, Container)

            with suppress(ValueError):
                self.parent.remove(self)

        animator.animate_attr(
            target=self,
            attr="_fade_progress",
            start=self.width,
            end=0,
            duration=150,
            on_finish=_on_finish,
        )

    def get_lines(self) -> list[str]:
        """Gets the lines from Button, and cuts them off at self._fade_progress"""

        return [self.styles.label(self.label[: self._fade_progress])]


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

        if self.show_output:
            self._add_widget(self._output)

    @property
    def selectables_length(self) -> int:
        """Returns either the button count or 1."""

        return max(super().selectables_length, 1)

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

            button = _FadeInButton(f"{color:^5}", width=5)
            button.styles.label = f"black @{color}"
            self.chosen.lazy_add(button)

            return True

        return False

    def get_lines(self) -> list[str]:
        """Updates self._output and gets widget lines."""

        if self.show_output and self._matrix.selected_pixel is not None:
            _, color = self._matrix.selected_pixel
            if len(color) == 0:
                return super().get_lines()

            color_obj = str_to_color(color)
            rgb = color_obj.rgb
            hex_ = color_obj.hex
            lines: list[Widget] = [
                Label(f"[black @{color}] {color} [/ {color}] {color}"),
                Label(
                    f"[{color} bold]Here[/bold italic] is "
                    + "[/italic underline]some[/underline dim] example[/dim] text"
                ),
                Label(),
                Label(
                    f"RGB: [{';'.join(map(str, rgb))}]"
                    + f"rgb({rgb[0]:>3}, {rgb[1]:>3}, {rgb[2]:>3})"
                ),
                Label(f"HEX: [{hex_}]{hex_}"),
            ]
            self._output.set_widgets(lines + [Label(), self.chosen])

            return super().get_lines()

        return super().get_lines()
