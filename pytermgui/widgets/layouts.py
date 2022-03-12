"""The module containing all of the layout-related widgets."""

# The widgets defined here are quite complex, so I think unrestricting them this way
# is more or less reasonable.
# pylint: disable=too-many-instance-attributes, too-many-lines, too-many-public-methods

from __future__ import annotations

from itertools import zip_longest
from typing import Any, Callable, Iterator, cast

from ..ansi_interface import MouseAction, MouseEvent, clear, reset, terminal
from ..context_managers import cursor_at
from ..enums import (
    CenteringPolicy,
    HorizontalAlignment,
    SizePolicy,
    VerticalAlignment,
    Overflow,
)
from ..exceptions import WidthExceededError
from ..helpers import real_length
from ..input import keys
from . import boxes
from . import styles as w_styles
from .base import Widget


class Container(Widget):
    """A widget that displays other widgets, stacked vertically."""

    chars: dict[str, w_styles.CharType] = {
        "border": ["| ", "-", " |", "-"],
        "corner": [""] * 4,
    }

    styles = {
        "border": w_styles.MARKUP,
        "corner": w_styles.MARKUP,
        "fill": w_styles.BACKGROUND,
    }

    keys = {
        "next": {keys.DOWN, keys.CTRL_N, "j"},
        "previous": {keys.UP, keys.CTRL_P, "k"},
        "scroll_down": {keys.SHIFT_DOWN, "J"},
        "scroll_up": {keys.SHIFT_UP, "K"},
    }

    serialized = Widget.serialized + ["centered_axis"]
    vertical_align = VerticalAlignment.CENTER
    allow_fullscreen = True

    overflow = Overflow.get_default()

    # TODO: Add `WidgetConvertible`? type instead of Any
    def __init__(self, *widgets: Any, **attrs: Any) -> None:
        """Initialize Container data"""

        super().__init__(**attrs)

        # TODO: This is just a band-aid.
        if "width" not in attrs:
            self.width = 40

        self._widgets: list[Widget] = []
        self.centered_axis: CenteringPolicy | None = None

        self._scroll_offset = 0
        self._max_scroll = 0
        self._prev_screen: tuple[int, int] = (0, 0)
        self._has_printed = False

        self.styles = type(self).styles.copy()
        self.chars = type(self).chars.copy()

        for widget in widgets:
            self._add_widget(widget)

        if "box" in attrs:
            self.box = attrs["box"]

        self._drag_target: Widget | None = None

    @property
    def sidelength(self) -> int:
        """Gets the length of left and right borders combined.

        Returns:
            An integer equal to the `pytermgui.helpers.real_length` of the concatenation of
                the left and right borders of this widget, both with their respective styles
                applied.
        """

        chars = self._get_char("border")
        style = self._get_style("border")
        if not isinstance(chars, list):
            return 0

        left_border, _, right_border, _ = chars
        return real_length(style(left_border) + style(right_border))

    @property
    def selectables(self) -> list[tuple[Widget, int]]:
        """Gets all selectable widgets and their inner indices.

        This is used in order to have a constant reference to all selectable indices within this
        widget.

        Returns:
            A list of tuples containing a widget and an integer each. For each widget that is
            withing this one, it is added to this list as many times as it has selectables. Each
            of the integers correspond to a selectable_index within the widget.

            For example, a Container with a Button, InputField and an inner Container containing
            3 selectables might return something like this:

            ```
            [
                (Button(...), 0),
                (InputField(...), 0),
                (Container(...), 0),
                (Container(...), 1),
                (Container(...), 2),
            ]
            ```
        """

        _selectables: list[tuple[Widget, int]] = []
        for widget in self._widgets:
            if not widget.is_selectable:
                continue

            for i, (inner, _) in enumerate(widget.selectables):
                _selectables.append((inner, i))

        return _selectables

    @property
    def selectables_length(self) -> int:
        """Gets the length of the selectables list.

        Returns:
            An integer equal to the length of `self.selectables`.
        """

        return len(self.selectables)

    @property
    def selected(self) -> Widget | None:
        """Returns the currently selected object

        Returns:
            The currently selected widget if selected_index is not None,
            otherwise None.
        """

        # TODO: Add deeper selection

        if self.selected_index is None:
            return None

        if self.selected_index >= len(self.selectables):
            return None

        return self.selectables[self.selected_index][0]

    @property
    def box(self) -> boxes.Box:
        """Returns current box setting

        Returns:
            The currently set box instance.
        """

        return self._box

    @box.setter
    def box(self, new: str | boxes.Box) -> None:
        """Applies a new box.

        Args:
            new: Either a `pytermgui.boxes.Box` instance or a string
                analogous to one of the default box names.
        """

        if isinstance(new, str):
            from_module = vars(boxes).get(new)
            if from_module is None:
                raise ValueError(f"Unknown box type {new}.")

            new = from_module

        assert isinstance(new, boxes.Box)
        self._box = new
        new.set_chars_of(self)

    def __iadd__(self, other: object) -> Container:
        """Adds a new widget, then returns self.

        Args:
            other: Any widget instance, or data structure that can be turned
            into a widget by `Widget.from_data`.

        Returns:
            A reference to self.
        """

        self._add_widget(other)
        return self

    def __add__(self, other: object) -> Container:
        """Adds a new widget, then returns self.

        This method is analogous to `Container.__iadd__`.

        Args:
            other: Any widget instance, or data structure that can be turned
            into a widget by `Widget.from_data`.

        Returns:
            A reference to self.
        """

        self.__iadd__(other)
        return self

    def __iter__(self) -> Iterator[Widget]:
        """Gets an iterator of self._widgets.

        Yields:
            The next widget.
        """

        for widget in self._widgets:
            yield widget

    def __len__(self) -> int:
        """Gets the length of the widgets list.

        Returns:
            An integer describing len(self._widgets).
        """

        return len(self._widgets)

    def __getitem__(self, sli: int | slice) -> Widget | list[Widget]:
        """Gets an item from self._widgets.

        Args:
            sli: Slice of the list.

        Returns:
            The slice in the list.
        """

        return self._widgets[sli]

    def __setitem__(self, index: int, value: Any) -> None:
        """Sets an item in self._widgets.

        Args:
            index: The index to be set.
            value: The new widget at this index.
        """

        self._widgets[index] = value

    def __contains__(self, other: object) -> bool:
        """Determines if self._widgets contains other widget.

        Args:
            other: Any widget-like.

        Returns:
            A boolean describing whether `other` is in `self.widgets`
        """

        if other in self._widgets:
            return True

        for widget in self._widgets:
            if isinstance(widget, Container) and other in widget:
                return True

        return False

    def _add_widget(self, other: object, run_get_lines: bool = True) -> Widget:
        """Adds other to this widget.

        Args:
            other: Any widget-like object.
            run_get_lines: Boolean controlling whether the self.get_lines is ran.

        Returns:
            The added widget. This is useful when data conversion took place in this
            function, e.g. a string was converted to a Label.
        """

        if not isinstance(other, Widget):
            to_widget = Widget.from_data(other)
            if to_widget is None:
                raise ValueError(
                    f"Could not convert {other} of type {type(other)} to a Widget!"
                )

            other = to_widget

        # This is safe to do, as it would've raised an exception above already
        assert isinstance(other, Widget)

        self._widgets.append(other)
        if isinstance(other, Container):
            other.set_recursive_depth(self.depth + 2)
        else:
            other.depth = self.depth + 1

        other.get_lines()
        other.parent = self

        if run_get_lines:
            self.get_lines()

        return other

    def _get_aligners(
        self, widget: Widget, borders: tuple[str, str]
    ) -> tuple[Callable[[str], str], int]:
        """Gets an aligning method and position offset.

        Args:
            widget: The widget to align.
            borders: The left and right borders to put the widget within.

        Returns:
            A tuple of a method that, when called with a line, will return that line
            centered using the passed in widget's parent_align and width, as well as
            the horizontal offset resulting from the widget being aligned.
        """

        left, right = borders
        char = self._get_style("fill")(" ")

        def _align_left(text: str) -> str:
            """Align line to the left"""

            padding = self.width - real_length(left + right) - real_length(text)
            return left + text + padding * char + right

        def _align_center(text: str) -> str:
            """Align line to the center"""

            total = self.width - real_length(left + right) - real_length(text)
            padding, offset = divmod(total, 2)
            return left + (padding + offset) * char + text + padding * char + right

        def _align_right(text: str) -> str:
            """Align line to the right"""

            padding = self.width - real_length(left + right) - real_length(text)
            return left + padding * char + text + right

        if widget.parent_align == HorizontalAlignment.CENTER:
            total = self.width - real_length(left + right) - widget.width
            padding, offset = divmod(total, 2)
            return _align_center, real_length(left) + padding + offset

        if widget.parent_align == HorizontalAlignment.RIGHT:
            return _align_right, self.width - real_length(left) - widget.width

        # Default to left-aligned
        return _align_left, real_length(left)

    def _update_width(self, widget: Widget) -> None:
        """Updates the width of widget or self.

        This method respects widget.size_policy.

        Args:
            widget: The widget to update/base updates on.

        Raises:
            ValueError: Widget has SizePolicy.RELATIVE, but relative_width is None.
            WidthExceededError: Widget and self both have static widths, and widget's
                is larger than what is available.
        """

        available = self.width - self.sidelength

        if widget.size_policy == SizePolicy.FILL:
            widget.width = available
            return

        if widget.size_policy == SizePolicy.RELATIVE:
            if widget.relative_width is None:
                raise ValueError(f'Widget "{widget}"\'s relative width cannot be None.')

            widget.width = int(widget.relative_width * available)
            return

        if widget.width > available:
            if widget.size_policy == self.size_policy == SizePolicy.STATIC:
                raise WidthExceededError(
                    f"Widget {widget}'s static width of {widget.width}"
                    + f" exceeds its parent's available width {available}."
                    ""
                )

            if widget.size_policy == SizePolicy.STATIC:
                self.width = widget.width + self.sidelength

            else:
                widget.width = available

    def _apply_vertalign(
        self, lines: list[str], diff: int, padder: str
    ) -> tuple[int, list[str]]:
        """Insert padder line into lines diff times, depending on self.vertical_align.

        Args:
            lines: The list of lines to align.
            diff: The available height.
            padder: The line to use to pad.

        Returns:
            A tuple containing the vertical offset as well as the padded list of lines.

        Raises:
            NotImplementedError: The given vertical alignment is not implemented.
        """

        if self.vertical_align == VerticalAlignment.BOTTOM:
            for _ in range(diff):
                lines.insert(0, padder)

            return diff, lines

        if self.vertical_align == VerticalAlignment.TOP:
            for _ in range(diff):
                lines.append(padder)

            return 0, lines

        if self.vertical_align == VerticalAlignment.CENTER:
            top, extra = divmod(diff, 2)
            bottom = top + extra

            for _ in range(top):
                lines.insert(0, padder)

            for _ in range(bottom):
                lines.append(padder)

            return top, lines

        raise NotImplementedError(
            f"Vertical alignment {self.vertical_align} is not implemented for {type(self)}."
        )

    def lazy_add(self, other: object) -> None:
        """Adds `other` without running get_lines.

        This is analogous to `self._add_widget(other, run_get_lines=False).

        Args:
            other: The object to add.
        """

        self._add_widget(other, run_get_lines=False)

    def get_lines(self) -> list[str]:
        """Gets all lines by spacing out inner widgets.

        This method reflects & applies both width settings, as well as
        the `parent_align` field.

        Returns:
            A list of all lines that represent this Container.
        """

        def _get_border(left: str, char: str, right: str) -> str:
            """Gets a top or bottom border.

            Args:
                left: Left corner character.
                char: Border character filling between left & right.
                right: Right corner character.

            Returns:
                The border line.
            """

            offset = real_length(left + right)
            return left + char * (self.width - offset) + right

        lines: list[str] = []

        style = self._get_style("border")
        borders = [style(char) for char in self._get_char("border")]

        style = self._get_style("corner")
        corners = [style(char) for char in self._get_char("corner")]

        has_top_bottom = (real_length(borders[1]) > 0, real_length(borders[3]) > 0)

        align, offset = self._get_aligners(self, (borders[0], borders[2]))

        overflow = self.overflow
        # if overflow == Overflow.SCROLL:
        #     self.width -= self._scrollbar.width

        for widget in self._widgets:
            align, offset = self._get_aligners(widget, (borders[0], borders[2]))

            self._update_width(widget)

            widget.pos = (
                self.pos[0] + offset,
                self.pos[1] + len(lines) + (1 if has_top_bottom[0] else 0),
            )

            widget_lines: list[str] = []
            for line in widget.get_lines():
                if len(lines) + len(widget_lines) >= self.height - sum(has_top_bottom):
                    if overflow is Overflow.HIDE:
                        break

                    if overflow == Overflow.AUTO:
                        overflow = Overflow.SCROLL

                widget_lines.append(align(line))

            lines.extend(widget_lines)

        if overflow == Overflow.SCROLL:
            # TODO: Figure out a visual scrollbar
            #     self.width += self._scrollbar.width

            #     length = len(borders[2])
            #     start = self._scrollbar.position
            #     height = self.height - sum(has_top_bottom)

            #     self._scrollbar.height = height
            #     scrollbar = self._scrollbar.get_lines()
            #
            # new_lines = []
            # for i, line in enumerate(lines[start : start + height]):
            #     offset = len(line) - length
            #     new_lines.append(line[:offset] + scrollbar[i] + line[offset:])

            # lines = new_lines

            self._max_scroll = len(lines) - self.height + sum(has_top_bottom)
            height = self.height - sum(has_top_bottom)

            self._scroll_offset = max(0, min(self._scroll_offset, len(lines) - height))
            lines = lines[self._scroll_offset : self._scroll_offset + height]

        elif overflow == Overflow.RESIZE:
            self.height = len(lines) + sum(has_top_bottom)

        vertical_offset, lines = self._apply_vertalign(
            lines, self.height - len(lines) - sum(has_top_bottom), align("")
        )

        for widget in self._widgets:
            widget.pos = (widget.pos[0], widget.pos[1] + vertical_offset)

            # TODO: This is wasteful.
            widget.get_lines()

        if has_top_bottom[0]:
            lines.insert(0, _get_border(corners[0], borders[1], corners[1]))

        if has_top_bottom[1]:
            lines.append(_get_border(corners[3], borders[3], corners[2]))

        self.height = len(lines)
        return lines

    def set_widgets(self, new: list[Widget]) -> None:
        """Sets new list in place of self._widgets.

        Args:
            new: The new widget list.
        """

        self._widgets = []
        for widget in new:
            self._add_widget(widget)

    def serialize(self) -> dict[str, Any]:
        """Serializes this Container, adding in serializations of all widgets.

        See `pytermgui.widgets.base.Widget.serialize` for more info.

        Returns:
            The dictionary containing all serialized data.
        """

        out = super().serialize()
        out["_widgets"] = []

        for widget in self._widgets:
            out["_widgets"].append(widget.serialize())

        return out

    def pop(self, index: int = -1) -> Widget:
        """Pops widget from self._widgets.

        Analogous to self._widgets.pop(index).

        Args:
            index: The index to operate on.

        Returns:
            The widget that was popped off the list.
        """

        return self._widgets.pop(index)

    def remove(self, other: Widget) -> None:
        """Remove widget from self._widgets

        Analogous to self._widgets.remove(other).

        Args:
            widget: The widget to remove.
        """

        return self._widgets.remove(other)

    def set_recursive_depth(self, value: int) -> None:
        """Set depth for this Container and all its children.

        All inner widgets will receive value+1 as their new depth.

        Args:
            value: The new depth to use as the base depth.
        """

        self.depth = value
        for widget in self._widgets:
            if isinstance(widget, Container):
                widget.set_recursive_depth(value + 1)
            else:
                widget.depth = value

    def select(self, index: int | None = None) -> None:
        """Selects inner subwidget.

        Args:
            index: The index to select.

        Raises:
            IndexError: The index provided was beyond len(self.selectables).
        """

        # Unselect all sub-elements
        for other in self._widgets:
            if other.selectables_length > 0:
                other.select(None)

        if index is not None:
            index = max(0, min(index, len(self.selectables) - 1))
            widget, inner_index = self.selectables[index]
            widget.select(inner_index)

        self.selected_index = index

    def scroll(self, offset: int) -> int:
        """Scrolls to given offset, returns the new scroll_offset.

        Args:
            offset: The amount to scroll by. Positive offsets scroll down,
                negative up.

        Returns:
            The new scroll offset.
        """

        self._scroll_offset = min(
            max(0, self._scroll_offset + offset), self._max_scroll
        )

        return self._scroll_offset

    def scroll_end(self, end: int) -> int:
        """Scrolls to either top or bottom end of this object.

        Args:
            end: The offset to scroll to. 0 goes to the very top, -1 to the
                very bottom.

        Returns:
            The new scroll offset.
        """

        if end == 0:
            self._scroll_offset = 0

        elif end == -1:
            self._scroll_offset = self._max_scroll

        return self._scroll_offset

    def center(
        self, where: CenteringPolicy | None = None, store: bool = True
    ) -> Container:
        """Centers this object to the given axis.

        Args:
            where: A CenteringPolicy describing the place to center to
            store: When set, this centering will be reapplied during every
                print, as well as when calling this method with no arguments.

        Returns:
            This Container.
        """

        # Refresh in case changes happened
        self.get_lines()

        if where is None:
            # See `enums.py` for explanation about this ignore.
            where = CenteringPolicy.get_default()  # type: ignore

        centerx = centery = where is CenteringPolicy.ALL
        centerx |= where is CenteringPolicy.HORIZONTAL
        centery |= where is CenteringPolicy.VERTICAL

        pos = list(self.pos)
        if centerx:
            pos[0] = (terminal.width - self.width + 2) // 2

        if centery:
            pos[1] = (terminal.height - self.height + 2) // 2

        self.pos = (pos[0], pos[1])

        if store:
            self.centered_axis = where

        self._prev_screen = terminal.size

        return self

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Applies a mouse event on all children.

        Args:
            event: The event to handle

        Returns:
            A boolean showing whether the event was handled.
        """

        if event.action is MouseAction.RELEASE:
            # Force RELEASE event to be sent
            if self._drag_target is not None:
                self._drag_target.handle_mouse(
                    MouseEvent(MouseAction.RELEASE, event.position)
                )

            self._drag_target = None

        if self._drag_target is not None:
            return self._drag_target.handle_mouse(event)

        selectables_index = 0
        scrolled_pos = list(event.position)
        scrolled_pos[1] += self._scroll_offset
        event.position = (scrolled_pos[0], scrolled_pos[1])

        for widget in self._widgets:
            if widget.contains(event.position):
                handled = widget.handle_mouse(event)
                # This avoids too many branches from pylint.
                selectables_index += widget.selected_index or 0

                if event.action is MouseAction.LEFT_CLICK:
                    self._drag_target = widget

                    if handled and selectables_index < len(self.selectables):
                        self.select(selectables_index)

                if handled:
                    return handled

                break

            if widget.is_selectable:
                selectables_index += widget.selectables_length

        if self.overflow == Overflow.SCROLL:
            if event.action is MouseAction.SCROLL_UP:
                self.scroll(-1)
                return True

            if event.action is MouseAction.SCROLL_DOWN:
                self.scroll(1)
                return True

        return False

    def execute_binding(self, key: str) -> bool:
        """Executes a binding on self, and then on self._widgets.

        If a widget.execute_binding call returns True this function will too. Note
        that on success the function returns immediately; no further widgets are
        checked.

        Args:
            key: The binding key.

        Returns:
            True if any widget returned True, False otherwise.
        """

        if super().execute_binding(key):
            return True

        selectables_index = 0
        for widget in self._widgets:
            if widget.execute_binding(key):
                selectables_index += widget.selected_index or 0
                self.select(selectables_index)
                return True

            if widget.is_selectable:
                selectables_index += widget.selectables_length

        return False

    def handle_key(  # pylint: disable=too-many-return-statements, too-many-branches
        self, key: str
    ) -> bool:
        """Handles a keypress, returns its success.

        Args:
            key: A key str.

        Returns:
            A boolean showing whether the key was handled.
        """

        def _is_nav(key: str) -> bool:
            """Determine if a key is in the navigation sets"""

            return key in self.keys["next"] | self.keys["previous"]

        if self.selected is not None and self.selected.handle_key(key):
            return True

        scroll_actions = {
            **{key: 1 for key in self.keys["scroll_down"]},
            **{key: -1 for key in self.keys["scroll_up"]},
        }

        if key in self.keys["scroll_down"] | self.keys["scroll_up"]:
            for widget in self._widgets:
                if isinstance(widget, Container) and self.selected in widget:
                    widget.handle_key(key)

            self.scroll(scroll_actions[key])
            return True

        # Only use navigation when there is more than one selectable
        if self.selectables_length >= 1 and _is_nav(key):
            if self.selected_index is None:
                self.select(0)
                return True

            handled = False

            assert isinstance(self.selected_index, int)

            if key in self.keys["previous"]:
                # No more selectables left, user wants to exit Container
                # upwards.
                if self.selected_index == 0:
                    return False

                self.select(self.selected_index - 1)
                handled = True

            elif key in self.keys["next"]:
                # Stop selection at last element, return as unhandled
                new = self.selected_index + 1
                if new == len(self.selectables):
                    return False

                self.select(new)
                handled = True

            if handled:
                return True

        if key == keys.ENTER:
            if self.selected_index is None and self.selectables_length > 0:
                self.select(0)

            if self.selected is not None:
                self.selected.handle_key(key)
                return True

        for widget in self._widgets:
            if widget.execute_binding(key):
                return True

        return False

    def wipe(self) -> None:
        """Wipes the characters occupied by the object"""

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(real_length(line) * " ")

    def print(self) -> None:
        """Prints this Container.

        If the screen size has changed since last `print` call, the object
        will be centered based on its `centered_axis`.
        """

        if not terminal.size == self._prev_screen:
            clear()
            self.center(self.centered_axis)

        self._prev_screen = terminal.size

        if self.allow_fullscreen:
            self.pos = terminal.origin

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(line)

        self._has_printed = True

    def debug(self) -> str:
        """Returns a string with identifiable information on this widget.

        Returns:
            A str in the form of a class construction. This string is in a form that
            __could have been__ used to create this Container.
        """

        out = "Container("
        for widget in self._widgets:
            out += widget.debug() + ", "

        out = out.strip(", ")
        out += ", **attrs)"

        return out


class Splitter(Container):
    """A widget that displays other widgets, stacked horizontally."""

    chars: dict[str, list[str] | str] = {"separator": " | "}
    styles = {"separator": w_styles.MARKUP, "fill": w_styles.BACKGROUND}
    keys = {
        "previous": {keys.LEFT, "h", keys.CTRL_B},
        "next": {keys.RIGHT, "l", keys.CTRL_F},
    }

    parent_align = HorizontalAlignment.RIGHT

    def _align(
        self, alignment: HorizontalAlignment, target_width: int, line: str
    ) -> tuple[int, str]:
        """Align a line

        r/wordavalanches"""

        available = target_width - real_length(line)
        fill_style = self._get_style("fill")

        char = fill_style(" ")
        line = fill_style(line)

        if alignment == HorizontalAlignment.CENTER:
            padding, offset = divmod(available, 2)
            return padding, padding * char + line + (padding + offset) * char

        if alignment == HorizontalAlignment.RIGHT:
            return available, available * char + line

        return 0, line + available * char

    def get_lines(self) -> list[str]:
        """Join all widgets horizontally."""

        # An error will be raised if `separator` is not the correct type (str).
        separator = self._get_style("separator")(self._get_char("separator"))  # type: ignore
        separator_length = real_length(separator)

        target_width, error = divmod(
            self.width - (len(self._widgets) - 1) * separator_length, len(self._widgets)
        )

        vertical_lines = []
        total_offset = 0

        for widget in self._widgets:
            inner = []

            if widget.size_policy is SizePolicy.STATIC:
                target_width += target_width - widget.width
                width = widget.width
            else:
                widget.width = target_width + error
                width = widget.width
                error = 0

            aligned: str | None = None
            for line in widget.get_lines():
                # See `enums.py` for information about this ignore
                padding, aligned = self._align(
                    cast(HorizontalAlignment, widget.parent_align), width, line
                )
                inner.append(aligned)

            widget.pos = (
                self.pos[0] + padding + total_offset,
                self.pos[1] + (1 if type(widget).__name__ == "Container" else 0),
            )

            if aligned is not None:
                total_offset += real_length(inner[-1]) + separator_length

            vertical_lines.append(inner)

        lines = []
        for horizontal in zip_longest(*vertical_lines, fillvalue=" " * target_width):
            lines.append((reset() + separator).join(horizontal))

        return lines

    def debug(self) -> str:
        """Return identifiable information"""

        return super().debug().replace("Container", "Splitter", 1)
