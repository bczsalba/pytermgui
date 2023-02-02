"""Widgets to contain other widgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from ..ansi_interface import MouseAction, MouseEvent
from ..enums import HorizontalAlignment
from ..regex import real_length
from .base import Label, Widget
from .frames import Frame
from .layout import DimensionSource, Layout
from .styles import StyleManager


@dataclass
class ScrollData:
    """A simple dataclass to hold scrolling information."""

    horizontal: int
    vertical: int

    def apply_to(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Applies scroll offset to the given position."""

        return pos[0] + self.horizontal, pos[1] + self.vertical


class Group(Widget):
    """A widget to group other widgets together.

    Each group has a layout, which is used to structure its children.
    """

    layout: Layout
    scroll: ScrollData

    styles = StyleManager(frame=None)

    def __init__(
        self,
        *children: Any,
        frame: str | Type[Frame] = "Frameless",
        layout: Layout | None = None,
        **attrs: Any,
    ) -> None:
        """Initializes the group.

        Args:
            *children: Any number of objects that can be converted into widgets.
            frame: The frame this group should use. Can also be specified with the
                `group >> frames.Single` syntax.
            layout: The default layout instance to use.
            **attrs: Any other attributes to set on this object.
        """

        super().__init__(**attrs)

        self._children: list[Widget] = []
        self.scroll = ScrollData(0, 0)

        self.frame = frame
        self._layout_is_dirty = False
        self._mouse_target: Widget | None = None

        if layout is None:
            layout = Layout()

        layout.parent = self
        self._layout = layout

        for child in children:
            self.add(child)

    def __add__(self, other: Any) -> Group:
        """Calls `self.add(other)`"""

        return self.add(other)

    def __iadd__(self, other: Any) -> Group:
        """Calls `self.add(other)`"""

        return self.add(other)

    def __rshift__(self, other: Any) -> Frame:
        """Allows setting a frame without accessing the instance.

        This can be useful when using auto syntax:

        ```python
        group = (InputField() | Button("Send")) >> frames.Single
        ```
        """

        if not issubclass(other, Frame):
            raise ValueError(
                f"You can only right shift groups into frame types, not instances or {other!r}."
            )

        self.frame = other

        return self

    def __call__(self, **args: Any) -> Group:
        """Allows setting arbitrary attributes.

        This is only meant to be used in the auto syntax:

        ```python
        group = (get_left_widget() | get_right_widget())(padding=3)
        ```
        """

        for key, value in args.items():
            setattr(self, key, value)

        self.recreate_layout()
        return self

    def _align(self, lines: list[str]) -> list[str]:
        """Aligns the given lines based on this widget's `parent_align` attribute."""

        width = self.frame_content_size[0]

        def _align_left(line: str) -> str:
            return line + (width - real_length(line)) * " "

        def _align_center(line: str) -> str:
            right, extra = divmod(width - real_length(line), 2)
            left = right + extra

            return left * " " + line + right * " "

        def _align_right(line: str) -> str:
            return (width - real_length(line)) * " " + line

        aligner = {
            HorizontalAlignment.LEFT: _align_left,
            HorizontalAlignment.CENTER: _align_center,
            HorizontalAlignment.RIGHT: _align_right,
        }[
            0
        ]  # self.parent_align]

        aligned = []

        for line in lines:
            aligned.append(aligner(line))

        return aligned

    @property
    def frame(self) -> Frame:
        """Gets and sets this widget's frame.

        When setting, the frame type object is instantiated with this widget as its
        parent.
        """

        return self._frame

    @frame.setter
    def frame(self, new: str | Type[Frame]) -> None:
        """Sets this widget's frame."""

        if isinstance(new, str):
            new = Frame.from_name(new)

        self._frame = new(self)

    @property
    def frame_content_size(self) -> tuple[int, int]:
        """Returns the usable area within the frame."""

        return (
            self.width - (self.frame.left_size + self.frame.right_size),
            self.height - (self.frame.top_size + self.frame.bottom_size),
        )

    @property
    def framed_position(self) -> tuple[int, int]:
        """Gets the position of top-left corner of the area within the frame."""

        return self.pos[0] + self.frame.left_size, self.pos[1] + self.frame.top_size

    def add(self, other: Any) -> Group:
        """Adds a new child to the group.

        You can also use python operators to do this:

        ```python3
        group = Tower()
        group += MyWidget()

        row = (group + MyOtherWidget()) | MyThirdWidget
        ```
        """

        if not isinstance(other, Widget):
            other = Widget.from_data(other)

            if other is None:
                raise ValueError(
                    f"Could not convert {other!r} of type {type(other)} to a Widget."
                )

        self._children.append(other)

        self.add_to_layout(other)
        self._layout_is_dirty = True

        return self

    def add_to_layout(self, widget: Widget) -> None:
        """Adds a widget to our layout.

        Use this to implement custom layout behaviour. Default behaviour assigns the new
        widget to the first non-filled slot of our layout.
        """

        index = len([slot for slot in self._layout.slots if slot.content is not None])
        self._layout.assign(widget, index=index)

    def recreate_layout(self) -> None:
        """Creates a new layout and adds all children to it, using `add_to_layout`."""

        self._layout = Layout(self)

        for child in self._children:
            self.add_to_layout(child)

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handles mouse events."""

        if self._mouse_target is not None and event.action is MouseAction.RELEASE:
            self._mouse_target.handle_mouse(event)

        handled = False

        event.position = self.scroll.apply_to(event.position)

        for widget in self._children:
            if not widget.contains(event.position):
                continue

            if self._mouse_target not in [None, widget]:
                self._mouse_target.handle_mouse(
                    MouseEvent(MouseAction.RELEASE, event.position)
                )

            handled = widget.handle_mouse(event)
            self._mouse_target = widget

            if handled:
                break

        return handled

    def get_lines(self) -> list[str]:
        """Gets widgets' content aligned based on the layout."""

        self._layout.apply(origin=self.framed_position)

        return self._frame(self._align(self._layout.build_lines()))


class Tower(Group):
    """A group that stacks widgets vertically."""

    def add_to_layout(self, widget: Widget) -> None:
        if len(self._layout):
            self._layout.add_break()

        self._layout.add_slot(f"Row {len(self._layout)}")
        self._layout.assign(widget)


class Row(Group):
    """A group that stacks widgets horizontally."""

    padding: int = 0

    def add_to_layout(self, widget: Widget) -> None:
        if len(self._layout.slots) > 0 and self.padding > 0:
            self._layout.add_slot("Padding", width=self.padding)
            self._layout.assign(Label())

        self._layout.add_slot()
        self._layout.assign(widget)


class DefaultGroup(Group):
    """The default group that is applied when a widget without one is used.

    Allows setting dimensions using the `dimensions` attribute.
    """

    dimensions: tuple[DimensionSource, DimensionSource] = (1.0, 1.0)

    def add_to_layout(self, widget: Widget) -> None:
        width, height = self.dimensions

        self._layout.add_slot(width=width, height=height)
        self._layout.assign(widget)
