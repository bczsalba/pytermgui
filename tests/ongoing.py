import sys
from random import randint

from pytermgui import InputField, get_widget, MarkupFormatter, Container, keys, markup
from pytermgui.window_manager import WindowManager, Window
from pytermgui.cmd import MarkupApplication


def main() -> None:
    """Main method"""

    style = MarkupFormatter("[60]{item}")
    for obj in [Window, Container]:
        obj.set_style("corner", style)
        obj.set_style("border", style)

    manager = WindowManager()
    manager.bind("*", lambda *_: manager.show_targets())
    manager.bind(
        keys.CTRL_H,
        lambda *_: {
            markup.alias("wm-title", str(randint(0, 255))),
            markup.alias("wm-title", str(randint(0, 255))),
        },
    )

    app = MarkupApplication(manager)
    manager.add(app.construct_window())

    field: InputField

    window = (
        Window(width=50, title="root", is_modal=True)
        + f"[wm-title]This is a test window"
        + ""
        + {"Button": ["label"]}
        + {"Toggle": [["one", "two"]]}
        + {"Checkbox": [False]}
        + ""
        + InputField(id="field")
        + ""
        + (
            ["Submit", lambda *_: manager.alert(field.value)],
            ["Reset", lambda *_: setattr(field, "value", "")],
            ["Exit", lambda *_: manager.exit()],
        )
    ).center()

    manager.add(window)
    manager.bind(keys.CTRL_T, lambda manager, _: manager.add(window.copy()))

    field = get_widget("field")
    assert field is not None

    manager.run()


if __name__ == "__main__":
    main()
