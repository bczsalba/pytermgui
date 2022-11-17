import time

import pytermgui as ptg


def macro_time(fmt: str) -> str:
    return time.strftime(fmt)


ptg.tim.define("!time", macro_time)

with ptg.WindowManager() as manager:
    manager.layout.add_slot("Header", height=1)
    manager.add(
        ptg.Window(
            "Welcome to [!gradient(60) bold]PyTermGUI[/]!",
            box="EMPTY",
        )
    )

    manager.layout.add_slot("Body")
    manager.add(
        ptg.Window(
            "The current time is: \n\n[bold !time]%c",
            box="EMPTY",
        )
    )
