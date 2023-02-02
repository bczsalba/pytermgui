from __future__ import annotations

from random import randint
from typing import Any

import pytermgui as ptg
from pytermgui.widgets import Widget, frames
from pytermgui.widgets.group import DefaultGroup, Group, Row, Tower


class Placeholder(ptg.Widget):
    colors = {
        "hover": "primary",
        "left_click": "secondary",
        "right_click": "secondary+1",
        "left_drag": "tertiary",
        "right_drag": "tertiary+1",
        "release": "surface",
    }

    color = colors["release"]

    def __or__(self, other: Any) -> Group:
        if not isinstance(other, (Widget, Group)):
            raise ValueError("You can only | widgets with other widgets or groups")

        return Row(self, other)

    def __ror__(self, other: Any) -> Group:
        return type(self).__or__(other, self)

    def __truediv__(self, other: Any) -> Group:
        if not isinstance(other, (Widget, Group)):
            raise ValueError("You can only / widgets with other widgets or groups")

        return Tower(self, other)

    def __rtruediv__(self, other: Any) -> Group:
        return type(self).__truediv__(other, self)

    def handle_mouse(self, event: ptg.MouseEvent) -> bool:
        if super().handle_mouse(event):
            return True

        action = event.action.value
        if action in self.colors:
            self.color = self.colors[action]
            return True

        return False

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
        group = Tower(
            *[Row(Placeholder(), Placeholder(), Placeholder()) for _ in range(5)],
            height=10,
        )

        manager.add(
            ptg.Window(
                "---",
                # cool_group,
                group,
                "---",
                vertical_align=ptg.VerticalAlignment.TOP,
                width=60,
                height=10,
            ).center(),
        )
