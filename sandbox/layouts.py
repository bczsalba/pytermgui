import pytermgui as ptg

from pytermgui.window_manager.layouts import ROW_BREAK, Layout


fg = "#B7B6A4"
bg = "#A5A48D"
bg_blur = "#505049"

# ptg.Window.is_noblur = True
ptg.Window.styles.border__corner = f"{bg}"
ptg.Window.set_focus_styles(focused=("bg", "bg"), blurred=(f"{bg_blur}", f"{bg_blur}"))
ptg.Label.styles.value__fill = f"@{bg} #5B5948"

ptg.Splitter.set_char("separator", " ")
ptg.boxes.SINGLE.set_chars_of(ptg.Container)


def alert(self: ptg.WindowManager, *items, **attributes) -> ptg.Window:
    window = ptg.Window(*items, **attributes)
    window.is_modal = True
    window.center()
    self.add(window)

    return window


def setup_bindings(manager: ptg.WindowManager) -> None:
    manager.bind(
        ptg.keys.CTRL_N,
        lambda *_: alert(
            manager,
            "[/]Windows not defined in the layout will float!",
            box="DOUBLE",
            width=50,
            height=7,
        ),
    )

    manager.bind(ptg.keys.F11, lambda *_: manager.screenshot("Layout example"))


def header_body_footer_layout() -> Layout:
    """Returns a layout with a header, body & footer."""

    layout = Layout()

    # layout.add_slot("Header Left", width=0.2)
    layout.add_slot("Header", height=1)

    layout.add_break()

    layout.add_slot("Body")

    layout.add_break()

    layout.add_slot("Footer", height=1)
    layout.add_slot("Footer Right", width=0.1)

    return layout


def complex_layout() -> Layout:
    """Returns a layout mixing some static, relative & auto dimensions."""

    layout = Layout()
    layout.add_slot("Header", height=5)
    layout.add_slot("Header Left", width=0.2)

    layout.add_break()

    layout.add_slot("Body Left")
    layout.add_slot("Body", width=0.7)
    layout.add_slot("Body Right")

    layout.add_break()

    layout.add_slot("Footer", height=3)

    return layout


def main() -> None:
    with ptg.WindowManager() as manager:
        setup_bindings(manager)

        manager.layout = complex_layout()
        # manager.layout = header_body_footer_layout()
        # add_demo(manager)

        for slot in manager.layout.slots:
            if slot is ROW_BREAK:
                continue

            manager.add(ptg.Window(f"[bold] {slot.name} ", box="DOUBLE"), animate=False)

    for row in manager.layout.build_rows():
        print(row)

    with ptg.alt_buffer():
        manager.screenshot("Layout example", filename="layouts")


def add_demo(manager: ptg.WindowManager):
    """Adds demo environment to the given manager."""

    # Create header
    header = ptg.Window(box="EMPTY")
    splitter = ptg.Splitter()
    for _ in range(7):
        splitter.lazy_add("[bold] Header content ")

    header += splitter
    manager.add(header, animate=False)

    # Create body
    body = ptg.Window(
        ptg.ColorPicker(),
        ptg.Container(ptg.InputField(), "", ptg.Slider(), static_width=80),
        box="SINGLE",
    )

    manager.add(body, animate=False)

    # Create footer
    footer = ptg.Window(box="EMPTY")
    splitter = ptg.Splitter()
    for _ in range(7):
        splitter.lazy_add("[bold] footer content ")

    footer += splitter
    manager.add(footer, animate=False)

    manager.add(ptg.Window("Info", box="EMPTY"))


if __name__ == "__main__":
    main()
