
from pytermgui import Widget, Container, Button

import pytermgui as ptg
from pytermgui.widgets.overflow_preventer import overflow_preventer


def button_press(manager: ptg.WindowManager) -> None:
    modal = container.select(7)



container = ptg.Container()
for i in range(70):
    container.lazy_add(ptg.Button("BUTTON"))
window=ptg.Window(container)
with ptg.WindowManager() as manager:
    manager.layout.add_slot("Body")
    manager.add(window)
    overflow_preventer(container.height, window.height)
    #if(container.height > window.height):
        #raise ValueError("container size is too big and has overflown Window please reconfigure Container size")





