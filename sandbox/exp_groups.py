from random import randint

import pytermgui as ptg
from pytermgui.widgets.group import Group


class Tower(Group):
    def add_to_layout(self, widget: ptg.Widget) -> None:
        if len(self._layout):
            self._layout.add_break()

        self._layout.add_slot(f"Row {len(self._layout)}")
        self._layout.assign(widget)


class Splitter(Group):
    def add_to_layout(self, widget: ptg.Widget) -> None:
        self._layout.add_slot()
        self._layout.assign(widget)


class Placeholder(ptg.Widget):
    colors = {
        "hover": "skyblue",
        "click": "darkblue",
        "drag": "cadetblue",
        "idle": "#dddddd",
    }

    color = colors["idle"]

    def on_hover(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["hover"]

    def on_click(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["click"]

    def on_drag(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["drag"]

    def on_release(self, event: ptg.MouseEvent) -> bool:
        self.color = self.colors["idle"]

    def get_lines(self) -> int:
        width = self.width - 5

        if self.height == 0:
            return []

        lines = [f"[@{self.color} #auto]" + " " * width for _ in range(self.height)]

        lines[0] = f"[@{self.color} #auto]" + f"({self.pos})".center(width)

        label = ptg.Label(
            "\n".join(lines),
            width=self.width,
            height=self.height,
        )

        return label.get_lines()


if __name__ == "__main__":
    with ptg.WindowManager() as manager:
        group = Tower(frame="ASCII_X", height=25)

        manager.bind(
            "+",
            lambda *_: group.add(
                Splitter(
                    Tower(Placeholder(), frame="Light"),
                    Splitter(Placeholder(), Placeholder(), frame="Padded"),
                )
            ),
        )

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
