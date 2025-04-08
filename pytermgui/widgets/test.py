import pytermgui as ptg

import time

def macro_time(fmt: str) -> str:
    return time.strftime(fmt)


ptg.tim.define("!time", macro_time)

with ptg.WindowManager() as manager:
    manager.layout.add_slot("Body")
    manager.add(ptg.Window(ptg.Container(ptg.Button("ONE"), ptg.Button("TWO"), ptg.Button("THREE"), ptg.Button("FOUR"), ptg.Button("FIVE"),ptg.Collapsible("drop", ptg.Button("Six"), ptg.Button("Seven"),)), box="EMPTY"))


