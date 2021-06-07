"""
pytermgui.widget.base
---------------------
author: bczsalba


This submodule the basic elements this library provides.
"""

# these classes will have to have more than 7 attributes mostly.
# pylint: disable=too-many-instance-attributes

from __future__ import annotations
from copy import deepcopy
from typing import Optional, Type, Union, Iterator, Any

from ..exceptions import WidthExceededError
from ..context_managers import cursor_at
from ..parser import ansi_to_markup, optimize_ansi
from ..helpers import real_length
from ..ansi_interface import (
    screen_width,
    screen_height,
    screen_size,
    clear,
)
from .styles import (
    StyleCall,
    MarkupFormatter,
    apply_markup,
    overrideable_style,
    StyleType,
    DepthlessStyleType,
    CharType,
)


def _set_obj_or_cls_style(
    obj_or_cls: Union[Type[Widget], Widget], key: str, value: StyleType
) -> None:
    """Set the style of an object or class"""

    if not key in obj_or_cls.styles.keys():
        raise KeyError(f"Style {key} is not valid for {obj_or_cls}!")

    if not callable(value):
        raise ValueError(f"Style {key} for {type(obj_or_cls)} has to be a callable.")

    obj_or_cls.styles[key] = value


def _set_obj_or_cls_char(
    obj_or_cls: Union[Type[Widget], Widget], key: str, value: CharType
) -> None:
    """Set a char of an object or class"""

    if not key in obj_or_cls.chars.keys():
        raise KeyError(f"Char {key} is not valid for {obj_or_cls}!")

    obj_or_cls.chars[key] = value


class Widget:
    """The widget from which all UI classes derive from"""

    set_style = classmethod(_set_obj_or_cls_style)
    set_char = classmethod(_set_obj_or_cls_char)

    OVERRIDE: StyleType = overrideable_style
    styles: dict[str, StyleType] = {}
    chars: dict[str, CharType] = {}

    serialized: list[str] = [
        "id",
        "pos",
        "depth",
        "width",
        "height",
        "forced_width",
        "forced_height",
        "is_selectable",
        "selected_index",
        "selectables_length",
    ]

    # this class is loaded after this module,
    # and thus mypy doesn't see its existence.
    manager: Optional["_IDManager"] = None  # type: ignore

    def __init__(self, width: int = 0, pos: Optional[tuple[int, int]] = None) -> None:
        """Initialize universal data for objects"""

        self.set_style = lambda key, value: _set_obj_or_cls_style(self, key, value)
        self.set_char = lambda key, value: _set_obj_or_cls_char(self, key, value)

        self.forced_width: Optional[int] = None
        self.forced_height: Optional[int] = None

        self._width = width
        self.height = 1

        if pos is None:
            pos = 1, 1
        self.pos = pos

        self.depth = 0

        self.is_selectable = False
        self.selectables_length = 0
        self.selected_index: Optional[int] = None
        self.styles = type(self).styles.copy()
        self.chars = type(self).chars.copy()

        self._serialized_fields = type(self).serialized
        self._id: Optional[str] = None
        self._is_focused = False

    def __repr__(self) -> str:
        """Print self.debug() by default"""

        return self.debug()

    def __iter__(self) -> Iterator[Widget]:
        """Return self for iteration"""

        yield self

    @property
    def id(self) -> Optional[str]:  # pylint: disable=invalid-name
        """Getter for id property

        There is no better name for this."""

        return self._id

    @id.setter
    def id(self, value: str) -> None:  # pylint: disable=invalid-name
        """Register widget to idmanager

        There is no better name for this."""

        if self._id == value:
            return

        manager = Widget.manager
        assert manager is not None

        if (old := manager.get_id(self)) is not None:
            manager.deregister(old)

        self._id = value
        manager.register(self)

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

    def serialize(self) -> dict[str, Any]:
        """Serialize object based on type(object).serialized"""

        fields = self._serialized_fields

        out: dict[str, Any] = {"type": type(self).__name__}
        for key in fields:
            # detect styled values
            if key.startswith("*"):
                style = True
                key = key[1:]
            else:
                style = False

            value = getattr(self, key)

            # convert styled value into markup
            if style:
                style_call = self.get_style(key)
                if isinstance(value, list):
                    out[key] = [ansi_to_markup(style_call(char)) for char in value]
                else:
                    out[key] = ansi_to_markup(style_call(value))

                continue

            out[key] = value

        # the chars need to be handled separately
        out["chars"] = {}
        for key, value in self.chars.items():
            style_call = self.get_style(key)

            if isinstance(value, list):
                out["chars"][key] = [ansi_to_markup(style_call(char)) for char in value]
            else:
                out["chars"][key] = ansi_to_markup(style_call(value))

        return out

    def copy(self) -> Widget:
        """Copy widget into a new object"""

        return deepcopy(self)

    def focus(self) -> None:
        """Focus widget"""

        self._is_focused = True

    def blur(self) -> None:
        """Blur (unfocus) widget"""

        self._is_focused = False

    def get_style(self, key: str) -> DepthlessStyleType:
        """Try to get style"""

        style_method = self.styles[key]

        return StyleCall(self, style_method)

    def get_char(self, key: str) -> CharType:
        """Try to get char"""

        chars = self.chars[key]
        if isinstance(chars, str):
            return chars

        return chars.copy()

    def get_lines(self) -> list[str]:
        """Stub for widget.get_lines"""

        raise NotImplementedError(f"get_lines() is not defined for type {type(self)}.")

    def select(self, index: int) -> None:
        """Select part of self"""

        if not self.is_selectable:
            raise TypeError(f"Object of type {type(self)} is marked non-selectable.")

        index = min(max(0, index), self.selectables_length - 1)

        self.focus()
        self.selected_index = index

    def debug(self) -> str:
        """Debug identifiable information about object"""

        return type(self).__name__ + "()"


class Container(Widget):
    """The widget that serves as the outer parent to all other widgets"""

    # vertical aligment policies
    VERT_ALIGN_TOP = 0
    VERT_ALIGN_CENTER = 1
    VERT_ALIGN_BOTTOM = 2

    # horizontal aligment policies
    HORIZ_ALIGN_LEFT = 3
    HORIZ_ALIGN_CENTER = 4
    HORIZ_ALIGN_RIGHT = 5

    # centering policies
    CENTER_X = 6
    CENTER_Y = 7
    CENTER_BOTH = 8

    chars: dict[str, CharType] = {"border": ["| ", "-", " |", "-"], "corner": [""] * 4}

    styles: dict[str, StyleType] = {
        "border": apply_markup,
        "corner": apply_markup,
    }

    serialized = Widget.serialized + [
        "vert_align",
        "horiz_align",
        "_centered_axis",
    ]

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

        chars = self.get_char("border")
        style = self.get_style("border")
        if not isinstance(chars, list):
            return 0

        left_border, _, right_border, _ = chars
        return real_length(style(left_border) + style(right_border))

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

    def __iadd__(self, other: object) -> Container:
        """Call self._add_widget(other) and return self"""

        if not isinstance(other, Widget):
            raise NotImplementedError("You can only add widgets to a Container.")

        self._add_widget(other)
        return self

    def __add__(self, other: object) -> Container:
        """Call self._add_widget(other)"""

        self.__iadd__(other)
        return self

    def __iter__(self) -> Iterator[Widget]:
        """Iterate through self._widgets"""

        for widget in self._widgets:
            yield widget

    def __getitem__(self, sli: Union[int, slice]) -> Union[Widget, list[Widget]]:
        """Index in self._widget"""

        return self._widgets[sli]

    def __setitem__(self, index: int, value: Any) -> None:
        """Set item in self._widgets"""

        self._widgets[index] = value

    def _add_widget(self, other: Widget) -> None:
        """Add other to self._widgets"""

        if self.forced_width is not None and other.forced_width is not None:
            if self.forced_width < other.forced_width:
                raise ValueError(
                    "Object being added has a forced width that is larger than self."
                    + f" ({other.forced_width} > {self.forced_width})"
                )

        if other.forced_height is not None:
            other.height = other.forced_height

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

        self.height += other.height
        self.get_lines()

    def serialize(self) -> dict[str, Any]:
        """Serialize object"""

        out = super().serialize()
        out["_widgets"] = []

        for widget in self._widgets:
            out["_widgets"].append(widget.serialize())

        return out

    def pop(self, index: int) -> Widget:
        """Pop widget from self._widgets"""

        return self._widgets.pop(index)

    def remove(self, other: Widget) -> None:
        """Remove widget from self._widgets"""

        return self._widgets.remove(other)

    def set_recursive_depth(self, value: int) -> None:
        """Set depth for all children, recursively"""

        self.depth = value
        for widget in self._widgets:
            if isinstance(widget, Container):
                widget.set_recursive_depth(value + 1)
            else:
                widget.depth = value

    def get_lines(self) -> list[str]:  # pylint: disable=R0914, R0912, R0915
        """Get lines of all widgets

        This will soon be rewritten to be more future & reader proof."""

        def _apply_style(style: DepthlessStyleType, target: list[str]) -> list[str]:
            """Apply style to target list elements"""

            for i, char in enumerate(target):
                target[i] = style(char)

            return target

        corner_style = self.get_style("corner")
        border_style = self.get_style("border")

        border_char = self.get_char("border")
        assert isinstance(border_char, list)
        corner_char = self.get_char("corner")
        assert isinstance(corner_char, list)

        left, top, right, bottom = _apply_style(
            border_style,
            border_char,
        )
        t_left, t_right, b_right, b_left = _apply_style(
            corner_style,
            corner_char,
        )

        def _apply_forced_width(source: Widget, target: Widget) -> bool:
            """Apply source's forced_width attribute to target, return False if not possible."""

            if source.forced_width is not None and target.forced_width is None:
                width = screen_width()
                if source.forced_width > width:
                    raise WidthExceededError(
                        f"Element {source}'s forced_width ({source.forced_width})"
                        + f" will not fit in the current screen width ({width})."
                    )
                source.width = source.forced_width
                if target.width < source.width - self.sidelength:
                    target.width = source.width + self.sidelength

                return True

            return False

        def _border_line(border: str, left: str, right: str) -> str:
            """Create border line of border and corners"""

            _len = real_length(left + right)
            return optimize_ansi(left + border * int(self.width - _len) + right)

        def _pad_vertically(lines: list[str]) -> None:
            """Pad lines vertically"""

            if self.forced_height is None:
                return

            if self.vert_align is Container.VERT_ALIGN_TOP:
                for _ in range(self.forced_height - len(lines)):
                    lines.append(left + (self.width - self.sidelength) * " " + right)

            elif self.vert_align is Container.VERT_ALIGN_BOTTOM:
                for _ in range(self.forced_height - len(lines)):
                    lines.insert(0, left + (self.width - self.sidelength) * " " + right)

            elif self.vert_align is Container.VERT_ALIGN_CENTER:
                length = self.forced_height - len(lines)
                extra = length % 2

                for _ in range(length // 2):
                    lines.insert(0, left + (self.width - self.sidelength) * " " + right)
                    lines.append(left + (self.width - self.sidelength) * " " + right)

                for _ in range(extra):
                    lines.append(left + (self.width - self.sidelength) * " " + right)

        def _pad_horizontally(line: str) -> str:
            """Pad a line horizontally"""

            length = self.width - self.sidelength - real_length(line)

            if self.horiz_align is Container.HORIZ_ALIGN_LEFT:
                return line + length * " "

            if self.horiz_align is Container.HORIZ_ALIGN_RIGHT:
                return length * " " + line

            if self.horiz_align is Container.HORIZ_ALIGN_CENTER:
                extra = length % 2
                side = length // 2
                return (side + extra) * " " + line + side * " "

            raise NotImplementedError(
                f"Horizontal aligment {self.horiz_align} is not implemented"
            )

        lines: list[str] = []
        total_height = (
            screen_height() if self.forced_height is None else self.forced_height
        )

        maximum_width = screen_width() - self.sidelength

        if self.forced_width is None:
            self.width = min(self.width, screen_width() - 1)

        for widget in self._widgets:
            if len(lines) >= total_height:
                break

            container_offset = 1 if not isinstance(widget, Container) else 0

            if widget.forced_width is not None:
                widget.width = widget.forced_width

            # try apply forced width self->widget, then widget->self
            if not _apply_forced_width(self, widget):
                _apply_forced_width(widget, self)

            if widget.width >= self.width and not self.forced_width is not None:
                widget.width = min(widget.width, maximum_width - container_offset)
                self.width = widget.width + self.sidelength + container_offset
                self.width = min(self.width, screen_width() - 1)

            elif widget.forced_width is None:
                widget.width = self.width - self.sidelength - container_offset

            for line in widget.get_lines():
                if len(lines) >= total_height:
                    break

                bordered = left + _pad_horizontally(line) + right

                if (new := real_length(bordered)) != self.width:
                    if self.forced_width is None:
                        self.width = new + self.sidelength

                    else:
                        raise ValueError(
                            f"{widget} returned a line of invalid length"
                            + f' ({new} != {self.width}): \n"{bordered}".'
                        )

                lines.append(bordered)

        _pad_vertically(lines)
        if real_length(top) > 0:
            lines.insert(0, _border_line(top, t_left, t_right))

        if real_length(bottom) > 0:
            lines.append(_border_line(bottom, b_left, b_right))

        self.height = len(lines)

        return lines

    def select(self, index: Optional[int] = None) -> None:
        """Select inner object"""

        if index is None:
            if self.selected_index is None:
                raise ValueError(
                    "Cannot select nothing! "
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

        self.focus()

        # update self._prev_selected
        _ = self.selected

    def center(
        self, where: Optional[int] = CENTER_BOTH, store: bool = True
    ) -> Container:
        """Center object on given axis, store & reapply if `store`"""

        # refresh in case changes happened
        self.get_lines()

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

    def focus(self) -> None:
        """Focus all widgets"""

        for widget in self._widgets:
            widget.focus()

    def blur(self) -> None:
        """Focus all widgets"""

        for widget in self._widgets:
            widget.blur()

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

    def debug(self) -> str:
        """Return debug information about this object's widgets"""

        out = "Container(), widgets=["
        for widget in self._widgets:
            out += type(widget).__name__ + ", "

        out = out.strip(", ")
        out += "]"

        return out


class Splitter(Widget):
    """A widget that holds sub-widgets, and aligns them next to eachother"""

    chars: dict[str, CharType] = {
        "separator": " | ",
    }

    styles: dict[str, StyleType] = {
        "separator": apply_markup,
    }

    serialized = Widget.serialized + ["arrangement"]

    def __init__(self, arrangement: Optional[str] = None) -> None:
        """Initiate object"""

        super().__init__()
        self.arrangement = arrangement
        self._widgets: list[Widget] = []

    def __add__(self, other: object) -> Splitter:
        """Overload + operator"""

        return self.__iadd__(other)

    def __iadd__(self, other: object) -> Splitter:
        """Overload += operator"""

        if not isinstance(other, Widget):
            raise NotImplementedError("You can only add widgets to a Splitter.")

        self._add_widget(other)
        return self

    def __iter__(self) -> Iterator[Widget]:
        """Iterate through self._widgets"""

        for widget in self._widgets:
            yield widget

    def __getitem__(self, sli: Union[int, slice]) -> Union[Widget, list[Widget]]:
        """Index in self._widget"""

        return self._widgets[sli]

    def __setitem__(self, index: int, value: Any) -> None:
        """Set item in self._widgets"""

        self._widgets[index] = value

    def _add_widget(self, other: Widget) -> None:
        """Add an widget"""

        if other.forced_height is not None:
            other.height = other.forced_height

        if self.height is None:
            self.height += other.height

        self._widgets.append(other)

    def serialize(self) -> dict[str, Any]:
        """Serialize object"""

        out = super().serialize()
        out["_widgets"] = []

        for widget in self._widgets:
            out["_widgets"].append(widget.serialize())

        return out

    def get_lines(self) -> list[str]:
        """Get lines by joining all widgets

        This is not ideal. ListView-s don't work properly, and this object's
        width is not set correctly."""

        widgets = self._widgets

        if len(widgets) == 0:
            return []

        separator_style = self.get_style("separator")
        char = self.get_char("separator")
        assert isinstance(char, str), char
        separator = separator_style(char)

        if self.arrangement is None:
            widget_width = self.width // len(widgets)
            widget_width -= real_length((len(widgets) - 1) * separator)
            widths = [widget_width] * len(widgets)

        else:
            # there should be "fluid" widths, not just static ones.
            widths = [int(val) for val in self.arrangement.split(";")]

        for i, widget in enumerate(widgets):
            if widget.forced_width is None:
                try:
                    widget.width = widths[i]
                except IndexError as error:
                    raise ValueError(
                        "There were not enough widths supplied in the arrangement:"
                        + f" expected {len(widgets)}, got {len(widths)}."
                    ) from error

        lines = []
        widget_lines = [widget.get_lines() for widget in widgets]

        for horizontal in zip(*widget_lines):
            lines.append(separator.join(horizontal))

        self.width = max(real_length(line) for line in lines) - 1

        if self.forced_height is None:
            self.height = len(lines)

        return lines

    def debug(self) -> str:
        """Debug identifiable information about objects"""

        out = "Splitter(), widgets=["
        for widget in self._widgets:
            out += type(widget).__name__ + ", "

        out = out.strip(", ")
        out += "]"

        return out


class Prompt(Widget):
    """Selectable object showing a single value with a label"""

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


class Label(Widget):
    """Unselectable text object"""

    ALIGN_LEFT = 0
    ALIGN_CENTER = 1
    ALIGN_RIGHT = 2

    styles: dict[str, StyleType] = {
        "value": apply_markup,
    }

    serialized = Widget.serialized + [
        "*value",
        "align",
        "padding",
    ]

    def __init__(
        self,
        value: str = "",
        align: int = ALIGN_CENTER,
        padding: int = 0,
    ) -> None:
        """Set up object"""

        super().__init__()

        self.value = value
        self.align = align
        self.padding = padding
        self.width = real_length(value) + self.padding + 2

    def get_lines(self) -> list[str]:
        """Get lines of object"""

        value_style = self.get_style("value")
        lines = []

        if self.align is Label.ALIGN_CENTER:
            for line in self.value.split("\n"):
                line = value_style(line)
                padding = (self.width - real_length(line) - self.padding) // 2
                outline = (padding + self.padding + 1) * " " + line
                outline += (self.width - real_length(outline) + 1) * " "

                lines.append(outline)

        elif self.align is Label.ALIGN_LEFT:
            for line in self.value.split("\n"):
                line = value_style(line)
                padding = self.width - real_length(line) - self.padding + 1
                lines.append(self.padding * " " + line + padding * " ")

        elif self.align is Label.ALIGN_RIGHT:
            for line in self.value.split("\n"):
                line = value_style(line)
                lines.append(
                    (self.width - real_length(line) - self.padding + 1) * " "
                    + line
                    + self.padding * " "
                )

        return lines

    def get_align_string(self) -> str:
        """Get string of align value"""

        if self.align is Label.ALIGN_LEFT:
            align = "ALIGN_LEFT"

        elif self.align is Label.ALIGN_RIGHT:
            align = "ALIGN_RIGHT"

        elif self.align is Label.ALIGN_CENTER:
            align = "ALIGN_CENTER"

        return "Label." + align

    def debug(self) -> str:
        """Return identifiable information about object"""

        return f'Label(value="{self.value}", align={self.get_align_string()})'
