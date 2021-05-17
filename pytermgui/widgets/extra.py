"""
pytermgui.widgets.extra
------------------------
author: bczsalba


This submodule provides some extra widgets. The biggest difference
between these and the ones in .base is that these either fully rely on,
or at least partially use the classes provided in .base.
"""

# these classes will have to have more than 7 attributes mostly.
# pylint: disable=too-many-instance-attributes

from typing import Optional, Callable

from .base import (
    Container,
    Label,
    Widget,
    CharType,
    StyleType,
    default_foreground,
    default_background,
)

from ..input import keys
from ..ansi_interface import foreground256
from ..helpers import real_length


class ColorPicker(Container):
    """A Container that shows the 256 color table"""

    def __init__(self, grid_cols: int = 8) -> None:
        """Initialize object, set width"""

        super().__init__()

        self.grid_cols = grid_cols
        self.forced_width = self.grid_cols * 4 - 1 + self.sidelength
        self.width = self.forced_width

    def get_lines(self) -> list[str]:
        """Get color table lines"""

        chars = self.get_char("border")
        assert isinstance(chars, list)
        left_border, _, right_border, _ = chars

        lines = super().get_lines()
        last_line = lines.pop()

        for line in range(256 // self.grid_cols):
            buff = left_border

            for num in range(self.grid_cols):
                col = str(line * self.grid_cols + num)
                if col == "0":
                    buff += "    "
                    continue

                padding = 3 - len(col)
                buff += foreground256(padding * " " + col, col) + " "

            buff = buff[:-1]
            lines.append(buff + "" + right_border)

        lines.append(last_line)
        return lines

    def debug(self) -> str:
        """Return identifiable information about object"""

        return f"ColorPicker(grid_cols={self.grid_cols})"


class ProgressBar(Widget):
    """A widget showing Progress"""

    chars: dict[str, CharType] = {
        "fill": ["#"],
        "delimiter": ["[ ", " ]"],
    }

    styles: dict[str, StyleType] = {
        "fill": default_foreground,
        "delimiter": default_foreground,
    }

    def __init__(self, progress_function: Callable[[], float]) -> None:
        """Initialize object"""

        super().__init__()
        self.progress_function = progress_function

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        delimiter_style = self.get_style("delimiter")
        fill_style = self.get_style("fill")

        delimiter_chars = self.get_char("delimiter")
        fill_char = self.get_char("fill")[0]

        start, end = [delimiter_style(self.depth, char) for char in delimiter_chars]
        progress_float = min(self.progress_function(), 1.0)

        total = self.width - real_length(start + end)
        progress = int(total * progress_float) + 1
        middle = fill_style(self.depth, progress * fill_char)

        line = start + middle
        return [line + (self.width + 1 - real_length(line + end)) * " " + end]

    def debug(self) -> str:
        """Return identifiable information about object"""

        return f"ProgressBar(progress_function={self.progress_function})"


class ListView(Widget):
    """Allow selection from a list of options"""

    LAYOUT_HORIZONTAL = 0
    LAYOUT_VERTICAL = 1

    styles: dict[str, StyleType] = {
        "delimiter": default_foreground,
        "value": default_foreground,
        "highlight": default_background,
    }

    chars: dict[str, CharType] = {"delimiter": ["< ", " >"]}

    def __init__(
        self,
        options: list[str],
        layout: int = LAYOUT_VERTICAL,
        align: int = Label.ALIGN_CENTER,
        padding: int = 0,
    ) -> None:
        """Initialize object"""

        super().__init__()

        self.padding = padding
        self.options = options
        self.layout = layout
        self.align = align
        self._donor_label = Label(align=self.align)
        self._height = len(self.options)

        self.is_selectable = True
        self.selectables_length = len(options)

    def get_lines(self) -> list[str]:
        """Get lines to represent object"""

        lines = []

        value_style = self.get_style("value")
        highlight_style = self.get_style("highlight")
        delimiter_style = self.get_style("delimiter")

        chars = self.get_char("delimiter")
        start, end = [delimiter_style(self.depth, char) for char in chars]

        if self.layout is ListView.LAYOUT_HORIZONTAL:
            pass

        elif self.layout is ListView.LAYOUT_VERTICAL:
            label = self._donor_label
            label.padding = self.padding
            label.width = self.width

            for i, opt in enumerate(self.options):
                value = [start, value_style(self.depth, opt), end]

                # highlight_style needs to be applied to all widgets in value
                if self._is_focused and i == self.selected_index:
                    label.value = "".join(
                        highlight_style(self.depth, widget) for widget in value
                    )

                else:
                    label.value = "".join(value)

                lines += label.get_lines()

        return lines

    def get_layout_string(self) -> str:
        """Get layout string"""

        if self.layout is ListView.LAYOUT_HORIZONTAL:
            layout = "LAYOUT_HORIZONTAL"
        elif self.layout is ListView.LAYOUT_VERTICAL:
            layout = "LAYOUT_VERTICAL"

        return "ListView." + layout

    def debug(self) -> str:
        """Return identifiable information about object"""

        return (
            "ListView("
            + f"options={self.options}, "
            + f"layout={self.get_layout_string()}, "
            + f"align={self._donor_label.get_align_string()}"
            + ")"
        )


class InputField(Widget):
    """A Label that lets you display input"""

    styles: dict[str, StyleType] = {
        "value": default_foreground,
        "cursor": default_background,
        "highlight": Widget.OVERRIDE,
    }

    def __init__(self, value: str = "", prompt: str = "", tab_length: int = 4) -> None:
        """Initialize object"""

        super().__init__()
        self._selected_range: tuple[Optional[int], Optional[int]] = (None, None)
        self.prompt = prompt
        self.value = value + " "
        self.tab_length = tab_length
        self.cursor = real_length(value)
        self.width = 40

        self._donor_label = Label(align=Label.ALIGN_LEFT)
        self._donor_label.width = self.width
        self._donor_label.set_style("value", self.get_style("value"))

    @property
    def selected_value(self) -> Optional[str]:
        """Get text that is selected"""

        start, end = self._selected_range
        if any(value is None for value in [start, end]):
            return None

        return self.value[start:end]

    @property
    def cursor(self) -> int:
        """Return cursor of self"""

        return self._cursor

    @cursor.setter
    def cursor(self, value: int) -> None:
        """Set cursor"""

        self._cursor = min(max(0, value), real_length(self.value) - 1)

    def clear_value(self) -> None:
        """Reset value of field"""

        self.value = " "
        self.cursor = 1

    def clear_selected(self) -> None:
        """Reset self._selected"""

        self._selected_range = (None, None)

    def has_selection(self) -> bool:
        """Return if there is text selected"""

        return all(val is not None for val in self._selected_range)

    def get_lines(self) -> list[str]:
        """Return broken-up lines from object"""

        def _get_label_lines(buff: str) -> list[str]:
            """Get lines from donor label"""

            label = self._donor_label
            label.value = buff
            return label.get_lines()

        def _normalize_cursor(
            coords: tuple[Optional[int], Optional[int]]
        ) -> tuple[int, int]:
            """Figure out switching None positions and ordering"""

            start, end = coords
            if start is None or end is None:
                start = end = self.cursor

            elif start > end:
                start, end = end, start

            return start, end

        self._donor_label.width = self.width

        lines = []
        buff = ""
        value_style = self.get_style("value")
        cursor_style = self.get_style("cursor")
        highlight_style = self.get_style("highlight")

        # highlight_style is optional
        if highlight_style is Widget.OVERRIDE:
            highlight_style = cursor_style

        start, end = _normalize_cursor(self._selected_range)
        self.cursor = end

        for i, char in enumerate(self.prompt + self.value):
            charindex = i - real_length(self.prompt)

            if char == keys.RETURN:
                buff_list = list(buff)
                buff_end = ""

                if self._is_focused and charindex == self.cursor:
                    buff_end = cursor_style(self.depth, " ")

                lines += _get_label_lines("".join(buff_list) + buff_end)
                buff = ""
                continue

            # currently all lines visually have an extra " " at the end
            if real_length(buff) > self.width:
                lines += _get_label_lines(buff[:-1])

                if char == keys.RETURN:
                    char = " "

                buff = ""

            elif self._is_focused and charindex == self.cursor:
                buff += cursor_style(self.depth, char)

            elif self._is_focused and start <= charindex <= end:
                buff += highlight_style(self.depth, char)

            else:
                buff += value_style(self.depth, char)

        if len(buff) > 0:
            lines += _get_label_lines(buff)

        self._height = len(lines)

        return lines

    def select_range(self, rng: tuple[int, int]) -> None:
        """Overwrite select method to do a visual selection in range"""

        self._selected_range = rng

    def send(self, key: Optional[str]) -> None:
        """Send key to InputField"""

        valid_platform_keys = [
            keys.SPACE,
            keys.CTRL_J,
            keys.CTRL_I,
        ]

        if key is None:
            return

        if key == keys.BACKSPACE:
            if self.cursor <= 0:
                return

            left = self.value[: self.cursor - 1]
            right = self.value[self.cursor :]

            self.value = left + right
            self.send(keys.LEFT)

        elif key is keys.CTRL_I:
            for _ in range(self.tab_length):
                self.send(keys.SPACE)

        elif key in [keys.LEFT, keys.CTRL_B]:
            self.cursor -= 1

        elif key in [keys.RIGHT, keys.CTRL_F]:
            self.cursor += 1

        elif key in [keys.DOWN, keys.CTRL_N]:
            self.cursor += self.width + 1

        elif key in [keys.UP, keys.CTRL_P]:
            self.cursor -= self.width + 1

        # `keys.values()` might need to be renamed to something more like
        # `keys.escapes.values()`
        elif key in valid_platform_keys or (
            real_length(key) == 1 and not key in keys.values()
        ):
            left = self.value[: self.cursor]
            right = self.value[self.cursor :]

            self.value = left + key + right
            self.cursor += 1

    def debug(self) -> str:
        """Return identifiable information about object"""

        value = self.value if real_length(self.value) < 7 else "..."

        return (
            "InputField("
            + f'prompt="{self.prompt}", '
            + f'value="{value}", '
            + f"tab_length={self.tab_length}"
            + ")"
        )
