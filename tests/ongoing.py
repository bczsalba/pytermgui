import pytermgui as ptg


def main() -> None:
    """Main method."""

    root = ptg.Window()
    root.box = ptg.boxes.DOUBLE
    # root += "[210 bold]These are some test widgets"
    # root += ""

    root += ptg.ColorPicker()

    with ptg.WindowManager() as manager:
        manager.bind("*", lambda *_: manager.show_targets())
        manager.add(root)
        manager.run()


if __name__ == "__main__":
    main()
