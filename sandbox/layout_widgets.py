from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pytermgui import Container, Layout, Widget, real_length
from pytermgui.widgets.boxes import Box


@dataclass
class WidgetLayout:
    _layout: Layout = field(default_factory=lambda: Layout(adapt_to_terminal=False))

    def update(
        self,
        *,
        size: tuple[int, int] | None = None,
        origin: tuple[int, int] = None,
    ) -> None:
        """Resizes the layout.

        If the given size is the same as the current one nothing is done. Otherwise,
        the size is updated and layout is re-applied.
        """

        change = False
        if self._layout.size != size:
            self._layout.resize(size, apply=False)
            change = True

        if self._layout.origin != origin:
            self._layout.origin = origin
            change = True

        if change:
            self._layout.apply()

    def apply(self) -> None:
        """Applies the layout."""

        self._layout.apply()

    def add_widget(self, widget: Widget) -> None:
        """Adds a widget to the layout."""


class TowerLayout(WidgetLayout):
    """A layout that arranges widgets in a vertical stack.

    The width of each widget will be the maximum width available; the available height
    is divided equally amongst each item.
    """

    def add_widget(self, widget: Widget) -> None:
        self._layout.add_break()
        self._layout.add_slot()
        self._layout.assign(widget, apply=False)


class SplitLayout(WidgetLayout):
    """A layout that arranges widgets in a vertical stack.

    The width of each widget will be the maximum width available; the available height
    is divided equally amongst each item.
    """

    gutter = 1

    def add_widget(self, widget: Widget) -> None:
        if len(self._layout.slots) > 0:
            self._layout.add_slot(width=self.gutter)

        self._layout.add_slot()
        self._layout.assign(widget, apply=False)


class LayoutContainer(Container):
    def __init__(
        self, *widgets: Widget, layout: WidgetLayout, box: Box | str = "ROUNDED"
    ) -> None:
        super().__init__()

        self.layout = layout

        self._widgets = []
        for widget in widgets:
            self.add(widget)

        self.box = box

    @property
    def box(self) -> Box:
        return self._box

    @box.setter
    def box(self, new: Box | str) -> None:
        if isinstance(new, str):
            new = Box.from_string(new)

        self._box = new

    def add(self, widget: Widget) -> None:
        self._widgets.append(widget)
        self.layout.add_widget(widget)

    def get_lines(self) -> list[str]:
        # self.positioned_line_buffer = poslines = self._box.render(
        #     origin=self.pos, width=self.width, height=self.height
        # )

        # origin = (self.pos[0] + 1, self.pos[1] + 1)
        # size = (self.width - 2, self.height - 2)

        self.positioned_line_buffer = poslines = []
        size = (self.width, self.height)
        origin = self.pos
        self.layout.update(size=size, origin=origin)

        for widget in self._widgets:
            xpos, ypos = widget.pos

            for i, line in enumerate(widget.get_lines()):
                poslines.append(((xpos, ypos + i), line))

            poslines.extend(widget.positioned_line_buffer)

        return []

        heights = []
        for item in poslines:
            heights.append(item[0][1])

        min_y = min(heights)
        max_y = max(heights)

        return [""] * (max_y - min_y)


class Tower(LayoutContainer):
    def __init__(self, *widgets: Widget) -> None:
        super().__init__(*widgets, layout=TowerLayout())


class Split(LayoutContainer):
    def __init__(self, *widgets: Widget) -> None:
        super().__init__(*widgets, layout=SplitLayout())


if __name__ == "__main__":
    import time

    import pytermgui as ptg

    # container = LayoutContainer(
    #     ptg.Label("This is a layout test."),
    #     ptg.Label("[!debug-layout]Origin: {origin}, Size: {size} -- {timestamp}"),
    #     # ptg.ColorPicker(),
    #     LayoutContainer(
    #         ptg.Button("Test button 1", parent_align=1),
    #         ptg.Button("Test button 2", parent_align=1),
    #         layout=Split,
    #     ),
    #     ptg.Slider(),
    #     # layout=Split,
    # )

    container = Tower(
        ptg.Label(
            "[!debug-layout]Origin: {origin}, Size: {size}, Timestamp: {timestamp}"
        ),
        Split(
            Tower(
                ptg.Label("The [primary bold]left[/] side"),
                ptg.Label(),
                ptg.Button("The left button"),
                # box="DOUBLE",
            ),
            Tower(
                ptg.Label("The [primary bold]right[/] side"),
                ptg.Label(),
                ptg.Button("The right button"),
                # box="DOUBLE",
            ),
            # box="SINGLE",
        ),
        Tower(
            Split(
                ptg.Button("Left"),
                ptg.Button("Middle"),
                ptg.Button("Right"),
            )
        ),
    )

    container.bind("+", lambda *_: setattr(container, "height", container.height + 1))
    container.bind("-", lambda *_: setattr(container, "height", container.height - 1))

    container.width = 40
    container.height = 20

    ptg.tim.define(
        "!debug-layout",
        lambda item: item.format(
            origin=str(container.layout._layout.origin),
            size=str(container.layout._layout.size),
            timestamp=str(time.time()),
        ),
    )

    with ptg.WindowManager() as manager:
        manager.add(ptg.Window(container))
