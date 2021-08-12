import sys
from typing import Union
from pytermgui import (
    Widget,
    Container,
    Window,
    WindowManager,
    InputField,
    ColorPicker,
    get_widget,
    Toggle,
    alert,
    boxes,
    ansi,
    keys,
    auto,
)


def _handle_command(manager: WindowManager, command: str) -> None:
    """Handle a command from the command window"""

    keywords = {
        "get": get_widget,
        "dbg": lambda _id: get_widget(_id).debug(),
    }

    args = []
    for key in reversed(command.split()):
        if not key in keywords:
            args.append(key)
            continue

        args = [keywords[key](*args)]

    window = (
        Window() + f"[wm-title]Output of [/ 245 italic]{command}" + "" + str(args[0])
    ).center()

    window.bind(keys.ESC, lambda window, _: window.close())
    manager.add(window)
    manager.print()


def main() -> None:
    """Main method"""

    boxes.DOUBLE_TOP.set_chars_of(Window)

    manager = WindowManager()

    def _alert_new_value(value: Union[bool, str]) -> None:
        """Alert value change for buttons"""

        manager.alert("New value: [210 bold]" + str(value))

    manager.bind("*", lambda manager, _: manager.show_targets())
    manager.bind(keys.CTRL_W, lambda manager, _: manager.focused.close())

    field: InputField
    manager.add(
        (
            Window(width=50, title=" root ")
            + f"[wm-title]This is a test window"
            + ""
            + {"Button": ["label", lambda *_: manager.alert("Button pressed!")]}
            + {"Toggle": [["one", "two"], _alert_new_value]}
            + {"Checkbox": [False, _alert_new_value]}
            + ""
            + InputField(id="field")
            + ""
            + (
                ["Submit", lambda *_: manager.alert(field.value)],
                ["Reset", lambda *_: setattr(field, "value", "")],
                ["Exit", lambda *_: sys.exit()],
            )
        ).center()
    )

    manager.add(Window() + ColorPicker(16, id="cp").debug())

    field = get_widget("field")
    field.bind(keys.RETURN, lambda *_: manager.alert(field.value))

    command_window = (
        Window(forced_width=70)
        + auto("[wm-title]Enter a command!", parent_align=0)
        + ""
        + InputField(prompt="!", id="command_field")
        + ""
        + ["Run", lambda *_: None]
    ).center()

    command_field = get_widget("command_field")
    command_window.bind(keys.ESC, lambda window, _: window.close())
    manager.bind("!", lambda manager, _: {manager.add(command_window), manager.print()})

    command_field.bind(
        keys.RETURN, lambda *_: _handle_command(manager, command_field.value)
    )

    manager.run()


if __name__ == "__main__":
    main()
