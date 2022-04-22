import pytermgui as ptg

from common import FocusedWindowDebugger, MouseDebugger, set_default_styles


def main() -> None:
    with ptg.WindowManager() as manager:
        set_default_styles()
        manager.bind(
            ptg.keys.F11,
            lambda *_: manager.focused.toggle_fullscreen()
            if manager.focused is not None
            else None,
        )
        manager.bind(ptg.keys.CTRL_L, lambda *_: manager.compositor.redraw())
        scrollview = ptg.Container(overflow=ptg.Overflow.SCROLL, height=20, box="EMPTY")
        window = ptg.Window(scrollview)

        for i in range(256):
            scrollview.lazy_add(
                ptg.Button(
                    f"This is color index {i:>3}.",
                ).set_style("label", f"@{i}")
            )

        manager.add(window)
        # manager.add(FocusedWindowDebugger())
        # manager.add(MouseDebugger(manager))
        manager.run()


if __name__ == "__main__":
    main()
