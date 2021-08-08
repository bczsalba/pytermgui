import sys
from pytermgui import Window, WindowManager, InputField, get_widget, alert, boxes, ansi, keys, auto

def main() -> None:
    """Main method"""

    boxes.DOUBLE_TOP.set_chars_of(Window)

    manager = WindowManager()
    manager.bind("*", lambda *_: manager.show_targets())

    field: InputField

    manager.add(
        (
            Window(width=50)
            + f"[wm-title]This is a test window"
            + ""
            + InputField(id="field")
            + ""
            + (
                auto(["Submit", lambda *_: manager.alert(field.value)], id="submit"),
                ["Reset", lambda *_: setattr(field, "value", "")],
                ["Exit", lambda *_: sys.exit(0)],
            )
        ).center()
    )

    field = get_widget("field")
    field.bind(keys.RETURN, lambda _: manager.alert(field.value))

    manager.run()

if __name__ == "__main__":
    main()
