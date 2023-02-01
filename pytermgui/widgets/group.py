from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from ..ansi_interface import MouseAction, MouseEvent
from ..enums import HorizontalAlignment
from ..regex import real_length
from .base import Widget
from .frames import Frame
from .layout import Layout
from .styles import StyleManager


@dataclass
class ScrollData:
    horizontal: int
    vertical: int

    def apply_to(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Applies scroll offset to the given position."""

        return pos[0] + self.horizontal, pos[1] + self.vertical


class Group(Widget):
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
        return self.add(other)

    def __iadd__(self, other: Any) -> Group:
        return self.add(other)

    def _align(self, lines: list[str]) -> list[str]:
        """Aligns the given lines based on this widget's `parent_align` attribute."""

        width = self.frame_content_size[0]

        def _align_left(line: str) -> str:
            return line + (width - real_length(line)) * " "

        def _align_center(line: str) -> str:
            right, extra = divmod(width - real_length(line), 2)
            left = right + extra

            return left * f" " + line + right * " "

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
        return (
            self.width - (self.frame.left_size + self.frame.right_size),
            self.height - (self.frame.top_size + self.frame.bottom_size),
        )

    @property
    def framed_position(self) -> tuple[int, int]:
        return self.pos[0] + self.frame.left_size, self.pos[1] + self.frame.top_size

    def on_resize(self) -> None:
        self._layout_is_dirty = True

    def add(self, other: Any) -> Group:
        """Adds a new widget to this one."""

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

        The base Group doesn't make use of its layout. Use other classes, such as
        [Tower] or [Splitter] instead.
        """

        index = len([slot for slot in self._layout.slots if slot.content is not None])
        self._layout.assign(widget, index=index)

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
