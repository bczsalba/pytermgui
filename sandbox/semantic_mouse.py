from functools import reduce

import pytermgui as ptg


class MouseTile(ptg.Container):
    actions = [
        "left_click",
        "right_click",
        "left_drag",
        "right_drag",
        "scroll_up",
        "scroll_down",
        "release",
        "hover",
    ]

    def __init__(self, *, width: int = 4, height: int = 4, **attrs) -> None:
        super().__init__(overflow=ptg.Overflow.HIDE, box="EMPTY", **attrs)

        self.content = ptg.Label("No action")

        self.lazy_add(self.content)

        # self.static_width = width
        self.height = height

        for i, action in enumerate(self.actions):
            handler = lambda _, event, i=i: self._generic_handle_mouse(event, i + 1)

            setattr(self, f"on_{action}", handler.__get__(self))

    def _generic_handle_mouse(
        self,
        event: ptg.MouseEvent,
        color: int,
    ) -> bool:
        action = event.action.value

        if action == "release":
            self.styles.fill = ""
            self.content.value = "No action"
            return False

        self.styles.fill = f"@{color}"
        self.content.value = f"[inverse bold {color}] {action} @ {event.position}"

        return action.endswith("drag")


def _setup_placeholder(manager: ptg.WindowManager) -> None:
    manager.layout.add_slot()
    manager.layout.add_slot()

    box = ptg.boxes.Box(["---", "x", ""])

    manager += ptg.Window(
        *(tuple(MouseTile(height=1) for _ in range(5)) for _ in range(2)),
        *(tuple(MouseTile(height=3) for _ in range(5)) for _ in range(5)),
        *(tuple(MouseTile(height=10) for _ in range(5)) for _ in range(5)),
        overflow=ptg.Overflow.SCROLL,
        box=box,
    ).set_title(ptg.markup.parse("[75]Tiles"))

    manager += ptg.Window(
        MouseTile(height=ptg.terminal.height),
        overflow=ptg.Overflow.SCROLL,
        box=box,
    ).set_title(ptg.markup.parse("[75]Full-window"))


if __name__ == "__main__":
    with ptg.WindowManager() as manager:
        ptg.Splitter.set_char("separator", "")

        _setup_placeholder(manager)
