import pytermgui as ptg

with ptg.WindowManager() as manager:
    window = ptg.Window(
        "[error]Whoops!",
        "",
        "[error-2]We haven't gotten around to doing this yet.",
        "",
        (
            "[surface+2]If you see this in the wild, please raise an issue about it,\n"
            + " preferably including a screenshot of this window and its general context.\n\n"
            + "Thanks for reading the docs and ([italic]hopefully[/italic]) using the project!"
        ),
    )

    window.styles.border_focused__corner_focused = "error"
    manager.layout.add_slot()
    manager.add(window)
