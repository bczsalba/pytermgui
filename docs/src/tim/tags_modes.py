from pytermgui import Window, WindowManager
from pytermgui.markup import style_maps as sm

root = Window(
    *[f"[{name}]{name}[/]" for name in sm.STYLES],
    box="SINGLE",
).set_title("Available modes")

with WindowManager() as manager:
    manager.autorun = False

    manager.layout.add_slot()
    manager += root
