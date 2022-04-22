from __future__ import annotations

import pytermgui as ptg


class DebuggerWindow(ptg.Window):
    is_noblur = True
    overflow = ptg.Overflow.RESIZE

    def get_lines(self) -> list[str]:
        self._widgets = []
        for widget in self._get_widgets():
            self.lazy_add(widget)

        return super().get_lines()

    def _update_content(self) -> None:
        raise NotImplementedError


class FocusedWindowDebugger(DebuggerWindow):
    def _get_widgets(self) -> None:
        if self.manager is None or self.manager.focused is None:
            return []

        window = self.manager.focused

        return [
            ptg.Label("Focused window debugger", style="bold foreground1 background1"),
            "",
            {"Elements #": ptg.Label(str(len(window)), style="foreground2")},
            {
                "Dimensions": ptg.Label(
                    f"{window.width}x{window.height}", style="foreground2"
                )
            },
            {
                "Position": ptg.Label(
                    f"({window.pos[0]};{window.pos[1]})", style="foreground2"
                )
            },
            {"Rect": f"{window.rect}"},
        ]


class MouseDebugger(DebuggerWindow):
    _event: ptg.MouseEvent | None = None

    def __init__(self, manager: ptg.WindowManager, **attrs: Any) -> None:
        super().__init__(**attrs)

        manager.bind(ptg.MouseEvent, self.on_mouse_move)

    def on_mouse_move(self, _, event: ptg.MouseEvent) -> None:
        self._event = event

    def _get_widgets(self) -> None:
        if self._event is None:
            return []

        return [
            ptg.Label("Mouse debugger", style="bold foreground1 background1"),
            "",
            {"Action": str(self._event.action.name)},
            {"Position": str(self._event.position)},
        ]


def set_default_styles():
    ptg.tim.alias("foreground1", "#AEAEAE")
    ptg.tim.alias("foreground2", "#8E8E8E")
    ptg.tim.alias("background1", "@#161314")
    ptg.tim.alias("background2", "@#56494E")

    ptg.Label.styles = ptg.Label.styles.branch(ptg.Label)
    ptg.Label.styles.value = "foreground1 background1"

    ptg.Window.styles.fill = "foreground1 background1"
    ptg.Container.styles.fill = "foreground1 background1"
    ptg.Window.styles.border__corner = f"background1 #2C2628"

    ptg.Splitter.styles.fill__separator = "foreground1 background1"
    ptg.Splitter.set_char("separator", " │ ")

    box = ptg.boxes.Box([" ", " x ", " "])
    box.set_chars_of(ptg.Window)
    ptg.boxes.HEAVY.set_chars_of(ptg.Container)
