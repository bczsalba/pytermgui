import pytermgui as ptg

DBG_WIN = (
    ptg.Window(is_noblur=True)
    + "[210 bold]Mouse Debugger"
    + ""
    + {"Event:": ptg.Label("Nothing", id="dbg_event")}
    + {"Position:": ptg.Label("Nothing", id="dbg_pos")}
)


def update_debug_window(
    window: ptg.Window, event: tuple[ptg.MouseAction, tuple[int, int]]
) -> None:
    """Update mouse debug window"""

    # noStroke  ->  camelCase -- java, javascript, processing
    # no_stroke ->  snake_case -- python, c++, c
    # NoStroke  ->  PascalCase
    # no-stroke ->  kebab-case

    action, pos = event
    event_label = ptg.get_widget("dbg_event")
    pos_label = ptg.get_widget("dbg_pos")

    event_label.value = str(action)
    pos_label.value = str(pos)


def main() -> None:
    """Main method"""

    with open("tests/environment.yaml", "r") as file:
        namespace = ptg.YamlLoader().load(file)

    with ptg.WindowManager() as manager:
        manager.add(DBG_WIN)

        manager.bind("*", lambda *_: manager.show_targets())
        manager.bind(ptg.MouseEvent, update_debug_window)
        window = namespace.CriteriaWindow

        window += (
            ptg.Container()
            + ptg.Container(ptg.Button("Press me", lambda *_: manager.alert("AAAAA")))
            + ptg.Button("No, press me!", lambda *_: manager.alert("BBBBB"))
        )

        manager.add(window)
        manager.run()


if __name__ == "__main__":
    main()
