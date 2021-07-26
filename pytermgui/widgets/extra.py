"""
pytermgui.widgets.extra
------------------------
author: bczsalba


This submodule provides some extra widgets. The biggest difference
between these and the ones in .base is that these either fully rely on,
or at least partially use the classes provided in .base.
"""

# These classes will have to have more than 7 attributes mostly.
# pylint: disable=too-many-instance-attributes

from typing import Optional, Callable, Any

from .base import (
    Container,
    Label,
    Widget,
    Button,
    MouseCallback,
)

from .styles import (
    default_foreground,
    default_background,
    MarkupFormatter,
    apply_markup,
    StyleType,
    CharType,
)
from ..input import keys, getch
from ..ansi_interface import foreground, background
from ..helpers import real_length, strip_ansi


class ColorPicker(Container):
    """A Container that shows the 256 color table"""

    serialized = Widget.serialized + ["grid_cols"]

    def __init__(self, grid_cols: int = 8, **attrs: Any) -> None:
        """Initialize object, set width"""

        super().__init__(**attrs)

        self.grid_cols = grid_cols
        self.forced_width = self.grid_cols * 4 - 1 + self.sidelength
        self.width = self.forced_width

        self._layer_functions = [
            foreground,
            background,
        ]

        self.layer = 0

    def toggle_layer(self) -> None:
        """Toggle foreground/background"""

        self.layer = 1 if self.layer == 0 else 0

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

                buff += self._layer_functions[self.layer](f"{col:>3}", col) + " "

            buff = buff[:-1]
            lines.append(buff + "" + right_border)

        lines.append(last_line)

        return lines

    def debug(self) -> str:
        """Return identifiable information about object"""

        return f"ColorPicker(grid_cols={self.grid_cols})"


class Splitter(Container):
    """A Container-like object that allows stacking Widgets horizontally"""

    chars: dict[str, CharType] = {"separator": " | "}

    styles: dict[str, StyleType] = {
        "separator": apply_markup,
    }

    def __init__(self, *widgets: Widget, **attrs: Any) -> None:
        """Initialize Splitter, add given elements to it"""

        super().__init__(*widgets, **attrs)
        self.parent_align = Widget.PARENT_RIGHT

    @staticmethod
    def _get_aligner(widget: Widget) -> Callable[[str, int], str]:
        """Get aligner method for alignment value"""

        def _align_left(line: str, width: int) -> str:
            """Align string left"""

            difference = width - real_length(line)
            return line + difference * " "

        def _align_center(line: str, width: int) -> str:
            """Align string center"""

            difference, offset = divmod(width - real_length(line), 2)
            return (difference + offset) * " " + line + difference * " "

        def _align_right(line: str, width: int) -> str:
            """Align string right"""

            difference = width - real_length(line)
            return difference * " " + line

        if widget.parent_align is Widget.PARENT_LEFT:
            return _align_left

        if widget.parent_align is Widget.PARENT_CENTER:
            return _align_center

        if widget.parent_align is Widget.PARENT_RIGHT:
            return _align_right

        raise NotImplementedError(
            f"Parent-Alignment {widget.parent_align} is not implemented."
        )

    def get_lines(self) -> list[str]:
        """Get lines of all objects"""

        separator = self.get_char("separator")
        assert isinstance(separator, str)
        separator_length = real_length(separator)

        # target_width = self.width // len(self._widgets)

        lines = []
        widget_lines = []
        offset_buffer = 0
        current_offset = 0

        target_width = self.width // 2

        for widget in self._widgets:
            align = self._get_aligner(widget)

            if widget.forced_width is None:
                widget.width = target_width

            inner_lines = []
            for line in widget.get_lines():
                inner_lines.append(align(line, widget.width))

            widget_lines.append(inner_lines)

            current_offset = widget.width + separator_length
            offset_buffer += current_offset
            widget.pos = (self.pos[0] + offset_buffer, self.pos[1])

        for horizontal in zip(*widget_lines):
            lines.append(separator.join(horizontal))

        self.width = real_length(lines[-1])

        return lines


class ProgressBar(Widget):
    """A widget showing Progress"""

    chars: dict[str, CharType] = {
        "fill": ["#"],
        "delimiter": ["[ ", " ]"],
    }

    styles: dict[str, StyleType] = {
        "fill": apply_markup,
        "delimiter": apply_markup,
    }

    def __init__(self, progress_function: Callable[[], float], **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(**attrs)
        self.progress_function = progress_function

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        delimiter_style = self.get_style("delimiter")
        fill_style = self.get_style("fill")

        delimiter_chars = self.get_char("delimiter")
        fill_char = self.get_char("fill")[0]

        start, end = [delimiter_style(char) for char in delimiter_chars]
        progress_float = min(self.progress_function(), 1.0)

        total = self.width - real_length(start + end)
        progress = int(total * progress_float) + 1
        middle = fill_style(progress * fill_char)

        line = start + middle
        return [line + (self.width - real_length(line + end)) * " " + end]

    def debug(self) -> str:
        """Return identifiable information about object"""

        return f"ProgressBar(progress_function={self.progress_function})"


class ListView(Container):
    """Display a list of buttons"""

    styles = Container.styles | {
        "delimiter": apply_markup,
        "option": apply_markup,
        "highlight": default_background,
    }

    chars = Container.chars | {"delimiter": ["< ", " >"]}

    def __init__(
        self,
        options: list[str],
        onclick: Optional[MouseCallback] = None,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.set_char("border", [""] * 4)
        self.set_char("corner", [""] * 4)

        self.onclick = onclick
        self.options = options
        self.update_options()

    @property
    def selectables_length(self) -> int:
        """Return count of selectables"""

        return len(self.options)

    def update_options(self) -> None:
        """Refresh inner Button-s"""

        self._widgets = []

        for option in self.options:
            self._add_widget(
                Button(option, parent_align=self.parent_align, onclick=self.onclick)
            )


class InputField(Widget):
    """A Label that lets you display input"""

    styles: dict[str, StyleType] = {
        "value": default_foreground,
        "cursor": MarkupFormatter("[inverse]{item}"),
        "highlight": Widget.OVERRIDE,
    }

    serialized = Widget.serialized + [
        "value",
        "prompt",
        "cursor",
        "tab_length",
    ]

    def __init__(
        self,
        value: str = "",
        prompt: str = "",
        tab_length: int = 4,
        padding: int = 0,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)
        self._selected_range: tuple[Optional[int], Optional[int]] = (None, None)
        self.prompt = prompt
        self.padding = padding
        self.value = value + " "
        self.tab_length = tab_length
        self.cursor = real_length(value)
        self.width = 40

        self._selectables_length = 1

        self.parent_align = Widget.PARENT_LEFT

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

    def get_value(self, strip: bool = True) -> str:
        """Get stripped value of object"""

        value = strip_ansi(self.value)
        if strip:
            return value.strip()

        return value

    def clear_value(self) -> str:
        """Reset value of field, return old value"""

        old = strip_ansi(self.value).strip()
        self.value = " "
        self.cursor = 1

        return old

    def clear_selected(self) -> None:
        """Reset self._selected"""

        self._selected_range = (None, None)

    def has_selection(self) -> bool:
        """Return if there is text selected"""

        return all(val is not None for val in self._selected_range)

    def get_lines(self) -> list[str]:
        """Return broken-up lines from object"""

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

        lines = []
        buff = ""
        value_style = self.get_style("value")
        cursor_style = self.get_style("cursor")
        highlight_style = self.get_style("highlight")

        def _get_label_lines(buff: str) -> list[str]:
            """Get lines from donor label

            Note: This is temporary, the entire class will be rewritten."""

            return [buff]

        # highlight_style is optional
        if highlight_style.method is Widget.OVERRIDE:
            highlight_style = cursor_style

        start, end = _normalize_cursor(self._selected_range)
        self.cursor = end

        for i, char in enumerate(self.prompt + self.value):
            charindex = i - real_length(self.prompt)

            if char == keys.RETURN:
                buff_list = list(buff)
                buff_end = ""

                if self._is_focused and charindex == self.cursor:
                    buff_end = cursor_style(" ")

                lines += _get_label_lines("".join(buff_list) + buff_end)
                buff = ""
                continue

            # Currently all lines visually have an extra " " at the end
            if real_length(buff) > self.width:
                lines += _get_label_lines(buff[:-1])

                if char == keys.RETURN:
                    char = " "

                buff = ""

            elif self._is_focused and charindex == self.cursor:
                buff += cursor_style(char)

            elif self._is_focused and start <= charindex <= end:
                buff += highlight_style(char)

            else:
                buff += value_style(char)

        if len(buff) > 0:
            lines += _get_label_lines(buff)

        self.height = len(lines)
        self.define_mouse_target(0, 0, self.height).onclick = self.onclick

        return lines

    def select_range(self, rng: tuple[int, int]) -> None:
        """Overwrite select method to do a visual selection in range"""

        self._selected_range = rng

    def send(self, key: Optional[str]) -> None:
        """Send key to InputField"""

        def _find_newline(step: int) -> int:
            """Find newline in self.value stepping by `step`"""

            if step == -1:
                value = self.value[self.cursor :: step]
            else:
                value = self.value[self.cursor :: step]

            i = 0
            for i, char in enumerate(value):
                if char is keys.RETURN:
                    return i

            return i

        def _find_cursor_line() -> str:
            """Find line that cursor is in"""

            visited = 0
            for line in self.get_value().splitlines():
                new = real_length(line)
                visited += new + 1
                if visited - (1 if new > 0 else 0) >= self.cursor:
                    return line

            return ""

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
            self.cursor += _find_newline(1) + 1

        elif key in [keys.UP, keys.CTRL_P]:
            self.cursor -= max(_find_newline(-1), 1)
            line = _find_cursor_line()
            self.cursor -= real_length(line)

        # `keys.values()` might need to be renamed to something more like
        # `keys.escapes.values()`
        elif key in valid_platform_keys or (
            real_length(key) == 1 and not key in keys.values()
        ):
            left = self.value[: self.cursor]
            right = self.value[self.cursor :]

            self.value = left + key + right
            self.cursor += 1

    def select(self, index: Optional[int] = None) -> None:
        """Select object"""

        self.focus()

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


class Prompt(Widget):
    """Selectable object showing a single value with a label

    This is to be deprecated."""

    HIGHLIGHT_LEFT = 0
    HIGHLIGHT_RIGHT = 1
    HIGHLIGHT_ALL = 2

    styles: dict[str, StyleType] = {
        "label": apply_markup,
        "value": apply_markup,
        "delimiter": apply_markup,
        "highlight": MarkupFormatter("[inverse]{item}"),
    }

    chars: dict[str, CharType] = {
        "delimiter": ["< ", " >"],
    }

    serialized = Widget.serialized + [
        "*value",
        "*label",
        "highlight_target",
    ]

    def __init__(
        self,
        label: str = "",
        value: str = "",
        highlight_target: int = HIGHLIGHT_LEFT,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.label = label
        self.value = value
        self.highlight_target = highlight_target

        self.is_selectable = True
        self._selectables_length = 1

    def get_lines(self) -> list[str]:
        """Get lines for object"""

        self.mouse_targets = []

        label_style = self.get_style("label")
        value_style = self.get_style("value")
        delimiter_style = self.get_style("delimiter")
        highlight_style = self.get_style("highlight")

        delimiters = self.get_char("delimiter")
        assert isinstance(delimiters, list)

        start, end = delimiters
        label = label_style(self.label)

        value_list = [
            delimiter_style(start),
            value_style(self.value),
            delimiter_style(end),
        ]

        if self.selected_index is not None and self._is_focused:
            if self.highlight_target in [Prompt.HIGHLIGHT_LEFT, Prompt.HIGHLIGHT_ALL]:
                label = highlight_style(label)

                if self.highlight_target is Prompt.HIGHLIGHT_LEFT:
                    value = "".join(value_list)

            if self.highlight_target in [Prompt.HIGHLIGHT_RIGHT, Prompt.HIGHLIGHT_ALL]:
                value = "".join(highlight_style(item) for item in value_list)

        else:
            value = "".join(value_list)

        middle = " " * (self.width - real_length(label + value) + 1)

        if (
            self.selected_index is not None
            and self.highlight_target is Prompt.HIGHLIGHT_ALL
        ):
            middle = highlight_style(middle)

        button = self.define_mouse_target(0, 0, 1)
        button.onclick = self.onclick

        return [label + middle + value]

    def get_highlight_target_string(self) -> str:
        """Get highlight target string"""

        if self.highlight_target == Prompt.HIGHLIGHT_LEFT:
            target = "HIGHLIGHT_LEFT"

        elif self.highlight_target == Prompt.HIGHLIGHT_RIGHT:
            target = "HIGHLIGHT_RIGHT"

        elif self.highlight_target == Prompt.HIGHLIGHT_ALL:
            target = "HIGHLIGHT_ALL"

        return "Prompt." + target

    def debug(self) -> str:
        """String representation of self"""

        return (
            "Prompt("
            + "label={self.value}, "
            + f"value={self.value}, "
            + f"highlight_target={self.get_highlight_target_string()}"
            + ")"
        )


def alert(data: Any) -> None:
    """Create a dismissible dialogue and pause execution"""

    root = Container()
    root += Label("[210 italic bold]Alert!")
    root += Label()
    root += Label(str(data))

    root.center()
    root.print()
    getch()
    root.wipe()
