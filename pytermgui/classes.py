"""
pytermgui.classes
-----------------
author: bczsalba


This module provides the classes used by the module.
"""

# these classes will have to have more than 7 attributes mostly.
# pylint: disable=too-many-instance-attributes

from __future__ import annotations
from typing import Optional, Callable, Type, Union

from .helpers import real_length
from .context_managers import cursor_at
from .ansi_interface import (
    background16,
    screen_width,
    screen_height,
    screen_size,
    clear,
)

StyleType = Callable[[int, str], str]


def default_foreground(depth: int, item: str) -> str:
    """Default foreground style"""

    _ = depth
    return item


def default_background(depth: int, item: str) -> str:
    """Default background style"""

    return background16(item, 30 + depth)


class Widget:
    """The widget from which all UI classes derive from"""

    styles: dict[str, StyleType] = {}
    chars: dict[str, list[str]] = {}

    def __init__(self, width: int = 0, pos: Optional[tuple[int, int]] = None) -> None:
        """Initialize universal data for objects"""

        self.forced_width: Optional[int] = None
        self.forced_height: Optional[int] = None

        self._width = width
        self._height = 1

        if pos is None:
            pos = 1, 1
        self.pos = pos

        self.depth = 0

        self.is_selectable = False
        self.selectables_length = 0
        self.selected_index: Optional[int] = None
        self.styles = type(self).styles.copy()
        self.chars = type(self).chars.copy()

    def __repr__(self) -> str:
        """Print self.dbg() by default"""

        return self.dbg()

    @property
    def width(self) -> int:
        """Getter for width property"""

        return self._width

    @width.setter
    def width(self, value: int) -> None:
        """Setter for width property"""

        if self.forced_width is not None and value is not self.forced_width:
            raise TypeError(
                "It is impossible to manually set the width "
                + "of an object with a `forced_width` attribute."
            )

        self._width = value

    @property
    def height(self) -> int:
        """Getter for height property"""

        return self._height

    @height.setter
    def height(self, value: int) -> None:
        """Non-setter for height property"""

        raise TypeError(
            "`widget.height` is not settable, it is currently "
            + f"{self.height}. Use widget.forced_height instead."
        )

    @property
    def posx(self) -> int:
        """Return x position of object"""

        return self.pos[0]

    @posx.setter
    def posx(self, value: int) -> None:
        """Set x position of object"""

        if not isinstance(value, int):
            raise NotImplementedError("You can only set integers as object positions.")

        self.pos = (value, self.posy)

    @property
    def posy(self) -> int:
        """Return y position of object"""

        return self.pos[1]

    @posy.setter
    def posy(self, value: int) -> None:
        """Set y position of object"""

        if not isinstance(value, int):
            raise NotImplementedError("You can only set integers as object positions.")

        self.pos = (self.posx, value)

    @staticmethod
    def _set_style(
        cls_or_obj: Union[Type[Widget], Widget], key: str, value: StyleType
    ) -> None:
        """Protected method for setting styles"""

        if not key in cls_or_obj.styles.keys():
            raise KeyError(f"Style {key} is not valid for {cls_or_obj}!")

        if not callable(value):
            raise ValueError(
                f"Style {key} for {type(cls_or_obj)} has to be a callable."
            )

        cls_or_obj.styles[key] = value

    @staticmethod
    def _set_char(
        cls_or_obj: Union[Type[Widget], Widget], key: str, value: list[str]
    ) -> None:
        """Protected method for setting chars"""

        if not key in cls_or_obj.chars.keys():
            raise KeyError(f"Char {key} is not valid for {cls_or_obj}!")

        cls_or_obj.chars[key] = value

    @classmethod
    def set_class_style(cls, key: str, value: StyleType) -> None:
        """Set class_style key to value"""

        cls._set_style(cls, key, value)

    @classmethod
    def set_class_char(cls, key: str, value: list[str]) -> None:
        """Set class_char key to value"""

        cls._set_char(cls, key, value)

    def set_style(self, key: str, value: StyleType) -> None:
        """Set instance_style key to value"""

        self._set_style(self, key, value)

    def set_char(self, key: str, value: list[str]) -> None:
        """Set instance_char key to value"""

        self._set_char(self, key, value)

    def get_style(self, key: str) -> StyleType:
        """Try to get style"""

        return self.styles[key]

    def get_char(self, key: str) -> list[str]:
        """Try to get char"""

        return self.chars[key]

    def get_lines(self) -> list[str]:
        """Stub for widget.get_lines"""

        return [type(self).__name__]

    def select(self, index: int) -> None:
        """Select part of self"""

        if not self.is_selectable:
            raise TypeError(f"Object of type {type(self)} is marked non-selectable.")

        index = min(max(0, index), self.selectables_length - 1)
        self.selected_index = index

    def dbg(self) -> str:
        """Debug identifiable information about object"""

        return type(self).__name__ + "()"


class Container(Widget):
    """The widget that serves as the outer parent to all other widgets"""

    VERT_ALIGN_TOP = 0
    VERT_ALIGN_CENTER = 1
    VERT_ALIGN_BOTTOM = 2

    HORIZ_ALIGN_LEFT = 3
    HORIZ_ALIGN_CENTER = 4
    HORIZ_ALIGN_RIGHT = 5

    CENTER_X = 6
    CENTER_Y = 7
    CENTER_BOTH = 8

    chars: dict[str, list[str]] = {"border": ["| ", "-", " |", "-"], "corner": [""] * 4}

    styles: dict[str, StyleType] = {
        "border": default_foreground,
        "corner": default_foreground,
    }

    def __init__(
        self,
        width: int = 0,
        horiz_align: int = HORIZ_ALIGN_CENTER,
        vert_align: int = VERT_ALIGN_CENTER,
    ) -> None:
        """Initialize Container data"""

        super().__init__(width)
        self._widgets: list[Widget] = []
        self._selectables: dict[int, tuple[Widget, int]] = {}
        self._centered_axis: Optional[int] = None
        self._prev_selected: Optional[Widget] = None

        self._prev_screen: tuple[int, int] = (0, 0)

        self.vert_align = vert_align
        self.horiz_align = horiz_align

        self.styles = Container.styles.copy()
        self.chars = Container.chars.copy()

    @property
    def sidelength(self) -> int:
        """Returns length of left+right borders"""

        left_border, _, right_border, _ = self.chars["border"]
        return real_length(left_border + right_border)

    @property
    def selected(self) -> Optional[Widget]:
        """Return selected object"""

        if self.selected_index is None:
            return None

        data = self._selectables.get(self.selected_index)
        if data is None:
            return data

        self._prev_selected = data[0]
        return data[0]

    def __iadd__(self, other: object) -> Optional[Container]:
        """Call self._add_widget(other) and return self"""

        if not isinstance(other, Widget):
            raise NotImplementedError(
                "You can only add Widgets to other Widgets."
            )

        self._add_widget(other)
        return self

    def __add__(self, other: object) -> None:
        """Call self._add_widget(other)"""

        self.__iadd__(other)

    def _add_widget(self, other: Widget) -> None:
        """Add other to self._widgets"""

        if self.forced_width is not None and other.forced_width is not None:
            if self.forced_width < other.forced_width:
                raise ValueError(
                    "Object being added has a forced width that is larger than self."
                    + f" ({other.forced_width} > {self.forced_width})"
                )

        self._widgets.append(other)
        if isinstance(other, Container):
            other.set_recursive_depth(self.depth + 2)
        else:
            other.depth = self.depth + 1

        other.get_lines()

        if not len(keys := list(self._selectables)) > 0:
            sel_len = 0
        else:
            sel_len = max(keys) + 1

        for i in range(other.selectables_length):
            self._selectables[sel_len + i] = other, i

        self._height += other.height
        self.get_lines()

    def dbg(self) -> str:
        """Return dbg information about this object's widgets"""

        out = "Container(), widgets=["
        for widget in self._widgets:
            out += type(widget).__name__ + ", "

        out = out.strip(", ")
        out += "]"

        return out

    def set_recursive_depth(self, value: int) -> None:
        """Set depth for all children, recursively"""

        self.depth = value
        for widget in self._widgets:
            if isinstance(widget, Container):
                widget.set_recursive_depth(value + 1)
            else:
                widget.depth = value

    def get_lines(self) -> list[str]:
        """Get lines to represent the object"""

        # pylint: disable=too-many-locals, too-many-branches
        #  All the locals here are used,
        # reducing their number would make the code less readable
        # This method might need a refactor because of the branches
        # issue, but I don't see what could really be improved.

        def _apply_forced_width(source: Widget, target: Widget) -> bool:
            """Apply source's forced_width attribute to target, return False if not possible."""

            if source.forced_width is not None and not target.forced_width is not None:
                source.width = source.forced_width
                if source.width > target.width - self.sidelength:
                    target.width = source.width + self.sidelength

                return True

            return False

        def _create_border_line(left: str, middle: str, right: str) -> str:
            """Create border line by combining left + middle + right"""

            corner_len = real_length(left + right)

            # pad middle if theres no length
            if real_length(middle) == 0:
                middle = " "

            return (
                corner_style(self.depth, left)
                + border_style(self.depth, (self.width - corner_len) * middle)
                + corner_style(self.depth, right)
            )

        lines: list[str] = []

        borders = self.get_char("border")
        left_border, top_border, right_border, bottom_border = borders

        corners = self.get_char("corner")
        top_left, top_right, bottom_right, bottom_left = corners

        corner_style = self.get_style("corner")
        border_style = self.get_style("border")

        has_height_remaining = True
        for widget in self._widgets:
            if not has_height_remaining:
                break

            if not _apply_forced_width(widget, self):
                _apply_forced_width(self, widget)

            # Container()-s need an extra padding
            container_offset = 1 if not isinstance(widget, Container) else 0

            if widget.width >= self.width and not self.forced_width is not None:
                self.width = widget.width + self.sidelength + container_offset

            elif not widget.forced_width is not None:
                widget.width = self.width - self.sidelength - container_offset

            for line in widget.get_lines():
                if (
                    self.forced_height is not None
                    and len(lines) + 2 >= self.forced_height
                ):
                    has_height_remaining = False
                    break

                if (
                    self.forced_width is not None
                    and (other_len := real_length(line)) + self.sidelength
                    > self.forced_width
                ):
                    raise ValueError(
                        f"Object `{widget.dbg()}` "
                        + "could not be resized to self.forced_width. "
                        + f"({other_len} > {self.forced_width}) "
                    )

                if self.horiz_align is Container.HORIZ_ALIGN_CENTER:
                    side_padding = (
                        (self.width - real_length(line) - self.sidelength) // 2 * " "
                    )

                elif self.horiz_align is Container.HORIZ_ALIGN_LEFT:
                    side_padding = ""

                elif self.horiz_align is Container.HORIZ_ALIGN_RIGHT:
                    side_padding = (
                        self.width - real_length(line) - self.sidelength
                    ) * " "

                lines.append(
                    border_style(self.depth, left_border)
                    + side_padding
                    + line
                    + (self.width - self.sidelength - real_length(line + side_padding))
                    * " "
                    + border_style(self.depth, right_border)
                )

        if self.forced_height is not None:
            padding_range = self.forced_height - len(lines) - 2
            empty_line = (
                left_border + (self.width - self.sidelength) * " " + right_border
            )

            if self.vert_align is Container.VERT_ALIGN_TOP:
                for _ in range(padding_range):
                    lines.append(empty_line)

            elif self.vert_align is Container.VERT_ALIGN_CENTER:
                for _ in range(padding_range // 2):
                    lines.insert(0, empty_line)
                    lines.append(empty_line)

            elif self.vert_align is Container.VERT_ALIGN_BOTTOM:
                for _ in range(padding_range):
                    lines.insert(0, empty_line)

        lines.insert(0, _create_border_line(top_left, top_border, top_right))
        lines.append(_create_border_line(bottom_left, bottom_border, bottom_right))

        self._height = len(lines)
        return lines

    def select(self, index: Optional[int] = None) -> None:
        """Select inner object"""

        if index is None:
            if self.selected_index is None:
                raise ValueError(
                    "Cannot select nothing!"
                    + "Either give an argument to select() or set object.selected_index."
                )
            index = self.selected_index

        index = min(max(0, index), len(self._selectables) - 1)

        if (data := self._selectables.get(index)) is None:
            raise IndexError("Container selection index out of range")

        widget, inner_index = data
        widget.select(inner_index)
        self.selected_index = index

        if self._prev_selected is not None and self._prev_selected is not widget:
            self._prev_selected.selected_index = None

        # update self._prev_selected
        _ = self.selected

    def center(
        self, where: Optional[int] = CENTER_BOTH, store: bool = True
    ) -> Container:
        """Center object on given axis, store & reapply if `store`"""

        centerx = where in [Container.CENTER_X, Container.CENTER_BOTH]
        centery = where in [Container.CENTER_Y, Container.CENTER_BOTH]

        if centerx:
            self.posx = (screen_width() - self.width + 2) // 2

        if centery:
            self.posy = (screen_height() - self.height + 2) // 2

        if store:
            self._centered_axis = where

        self._prev_screen = screen_size()

        return self

    def wipe(self) -> None:
        """Wipe characters occupied by the object"""

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(real_length(line) * " ")

    def print(self) -> None:
        """Print object"""

        if not screen_size() == self._prev_screen:
            clear()
            self.center(self._centered_axis)

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(line)


class Label(Widget):
    """Unselectable text object"""

    ALIGN_LEFT = 0
    ALIGN_CENTER = 1
    ALIGN_RIGHT = 2

    styles: dict[str, StyleType] = {
        "value": default_foreground,
    }

    def __init__(self, value: str = "", align: int = ALIGN_CENTER) -> None:
        """Set up object"""

        super().__init__()

        self.value = value
        self.align = align
        self.padding = 0
        self.width = len(value) + self.padding

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        value_style = self.get_style("value")

        if self.align is Label.ALIGN_CENTER:
            padding = (self.width - real_length(self.value) - self.padding) // 2
            outline = (padding + self.padding + 1) * " " + self.value
            outline += (self.width - real_length(outline) + 1) * " "

            lines = [outline]

        elif self.align is Label.ALIGN_LEFT:
            padding = self.width - real_length(self.value) - self.padding + 1
            lines = [self.padding * " " + self.value + padding * " "]

        elif self.align is Label.ALIGN_RIGHT:
            lines = [
                (self.width - real_length(self.value) - self.padding + 1) * " "
                + self.value
                + self.padding * " "
            ]

        return [value_style(self.depth, line) for line in lines]

    def get_align_string(self) -> str:
        """Get string of align value"""

        if self.align is Label.ALIGN_LEFT:
            align = "ALIGN_LEFT"

        elif self.align is Label.ALIGN_RIGHT:
            align = "ALIGN_RIGHT"

        elif self.align is Label.ALIGN_CENTER:
            align = "ALIGN_CENTER"

        return "Label." + align

    def dbg(self) -> str:
        """Return identifiable information about object"""

        return f'Label(value="{self.value}", align={self.get_align_string()})'


class ListView(Widget):
    """Allow selection from a list of options"""

    LAYOUT_HORIZONTAL = 0
    LAYOUT_VERTICAL = 1

    styles: dict[str, StyleType] = {
        "delimiter": default_foreground,
        "value": default_foreground,
        "highlight": default_background,
    }

    chars: dict[str, list[str]] = {"delimiter": ["< ", " >"]}

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
        self.donor_label = Label(align=self.align)
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
            label = self.donor_label
            label.padding = self.padding
            label.width = self.width

            for i, opt in enumerate(self.options):
                value = [start, value_style(self.depth, opt), end]

                # highlight_style needs to be applied to all widgets in value
                if i == self.selected_index:
                    label.value = "".join(
                        highlight_style(self.depth, widget) for widget in value
                    )

                else:
                    label.value = "".join(value)

                lines += label.get_lines()

        self.width = max(real_length(l) for l in lines)

        return lines

    def get_layout_string(self) -> str:
        """Get layout string"""

        if self.layout is ListView.LAYOUT_HORIZONTAL:
            layout = "LAYOUT_HORIZONTAL"
        elif self.layout is ListView.LAYOUT_VERTICAL:
            layout = "LAYOUT_VERTICAL"

        return "ListView." + layout

    def dbg(self) -> str:
        """Return identifiable information about object"""

        return (
            "ListView("
            + f"options={self.options}, "
            + f"layout={self.get_layout_string()}, "
            + f"align={self.donor_label.get_align_string()}"
            + ")"
        )


class Prompt(Widget):
    """Selectable object showing a single value with a label"""

    HIGHLIGHT_LEFT = 0
    HIGHLIGHT_RIGHT = 1
    HIGHLIGHT_ALL = 2

    styles: dict[str, StyleType] = {
        "label": default_foreground,
        "value": default_foreground,
        "delimiter": default_foreground,
        "highlight": default_background,
    }

    chars: dict[str, list[str]] = {
        "delimiter": ["< ", " >"],
    }

    def __init__(
        self, label: str = "", value: str = "", highlight_target: int = HIGHLIGHT_LEFT
    ) -> None:
        """Initialize object"""

        super().__init__()
        self.label = label
        self.value = value
        self.highlight_target = highlight_target

        self.is_selectable = True
        self.selectables_length = 1

    def get_lines(self) -> list[str]:
        """Get lines for object"""

        label_style = self.get_style("label")
        value_style = self.get_style("value")
        delimiter_style = self.get_style("delimiter")
        highlight_style = self.get_style("highlight")

        delimiters = self.get_char("delimiter")

        start, end = delimiters
        label = label_style(self.depth, self.label)

        value_list = [
            delimiter_style(self.depth, start),
            value_style(self.depth, self.value),
            delimiter_style(self.depth, end),
        ]

        if self.selected_index is not None:
            if self.highlight_target in [Prompt.HIGHLIGHT_LEFT, Prompt.HIGHLIGHT_ALL]:
                label = highlight_style(self.depth, label)

                if self.highlight_target is Prompt.HIGHLIGHT_LEFT:
                    value = "".join(value_list)

            if self.highlight_target in [Prompt.HIGHLIGHT_RIGHT, Prompt.HIGHLIGHT_ALL]:
                value = "".join(
                    highlight_style(self.depth, item) for item in value_list
                )

        else:
            value = "".join(value_list)

        middle = " " * (self.width - real_length(label + value) + 1)

        if (
            self.selected_index is not None
            and self.highlight_target is Prompt.HIGHLIGHT_ALL
        ):
            middle = highlight_style(self.depth, middle)

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

    def dbg(self) -> str:
        """String representation of self"""

        return (
            "Prompt("
            + "label={self.value}, "
            + f"value={self.value}, "
            + f"highlight_target={self.get_highlight_target_string()}"
            + ")"
        )


class ProgressBar(Widget):
    """An widget showing Progress"""

    chars: dict[str, list[str]] = {
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

        start, end = [
            delimiter_style(self.depth, char) for char in delimiter_chars
        ]
        progress_float = min(self.progress_function(), 1.0)

        total = self.width - real_length(start + end)
        progress = int(total * progress_float)
        middle = fill_style(self.depth, progress * fill_char)

        line = start + middle
        return [line + (self.width - real_length(line + end)) * " " + end]
