from __future__ import annotations

from random import randint

import pytermgui as ptg
from pytermgui.widgets.group import Group
from pytermgui.widgets.layout import DimensionSource


class Tower(Group):
    def add_to_layout(self, widget: ptg.Widget) -> None:
        if len(self._layout):
            self._layout.add_break()

        self._layout.add_slot(f"Row {len(self._layout)}")
        self._layout.assign(widget)


class Splitter(Group):
    padding: int = 0

    def add_to_layout(self, widget: ptg.Widget) -> None:
        if len(self._children) > 0 and self.padding > 0:
            self._layout.add_slot("Padding", width=self.padding)
            self._layout.assign(ptg.Label())

        self._layout.add_slot()
        self._layout.assign(widget)


class Static(Group):
    dimensions: tuple[DimensionSource, DimensionSource] = (1.0, 1.0)

    def add_to_layout(self, widget: ptg.Widget) -> None:
        width, height = self.dimensions

        self._layout.add_slot()
        self._layout.add_slot(width=width, height=height)
        self._layout.assign(widget)
        self._layout.add_slot()


class Placeholder(ptg.Widget):
    colors = {
        # "hover": "skyblue",
        # "click": "darkblue",
        # "drag": "cadetblue",
        # "idle": "#dddddd",
        "hover": "primary",
        "left_click": "secondary",
        "right_click": "secondary+1",
        "left_drag": "tertiary",
        "right_drag": "tertiary+1",
        "idle": "surface",
    }

    color = colors["idle"]

    def on_hover(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["hover"]

    def on_left_click(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["left_click"]

    def on_right_click(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["right_click"]

    def on_left_drag(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["left_drag"]

    def on_right_drag(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["right_drag"]

    def on_release(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["idle"]

    def get_lines(self) -> int:
        width = self.width

        if self.height == 0:
            return []

        lines = [f"[@{self.color} #auto]" + " " * width for _ in range(self.height)]

        lines[0] = f"[@{self.color} #auto]" + f"{(self.width, self.height)}".center(
            width
        )

        label = ptg.Label(
            "\n".join(lines),
            width=self.width,
            height=self.height,
        )

        return label.get_lines()


if __name__ == "__main__":
    with ptg.WindowManager() as manager:
        group = Tower(frame="ASCII_X", height=25)

        # row = Placeholder() | (Placeholder() | Placeholder()) * {"frame": "Padded", "padding": 3}

        manager.bind(
            "1",
            lambda *_: group.add(
                Splitter(
                    Tower(Placeholder(), frame="Light"),
                    Splitter(Placeholder(), Placeholder(), padding=1),
                    frame="Heavy",
                )
            ),
        )

        manager.bind(
            "2",
            lambda *_: group.add(
                Splitter(ptg.Button("One"), ptg.Button("Two"), ptg.Button("Three"))
            ),
        )

        manager.bind(
            "3",
            lambda *_: group.add(
                Splitter(
                    Placeholder(),
                    Static(Placeholder(), dimensions=(0.7, 5), frame="Padded"),
                    Placeholder(),
                ),
            ),
        )

        manager.bind(
            "4",
            lambda *_: group.add(
                Splitter(
                    Placeholder(),
                    Placeholder(),
                    Placeholder(),
                    Placeholder(),
                    padding=1,
                )
            ),
        )

        cool_layout = ptg.widgets.layout.Layout()
        cool_layout.add_slot("Header", height=3)
        cool_layout.add_break()
        cool_layout.add_slot("Body")
        cool_layout.add_break()
        cool_layout.add_slot("Icon", height=5, width=10)
        cool_layout.add_slot("Footer", height=5)

        cool_group = Group(layout=cool_layout, width=30, height=30)
        manager.bind("+", lambda *_: cool_group.add(Tower(Placeholder())))

        # manager.add(ptg.Window(cool_group))

        manager.add(
            ptg.Window(
                "---",
                group,
                "---",
                vertical_align=ptg.VerticalAlignment.TOP,
                width=60,
                height=10,
            ).center(),
        )
