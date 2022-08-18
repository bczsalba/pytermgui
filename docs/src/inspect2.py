from pytermgui import Overflow, WindowManager
from pytermgui.cmd import InspectorWindow, _configure_widgets, _create_aliases

_create_aliases()
_configure_widgets()

termage.resize(100, 67)
window = InspectorWindow(overflow=Overflow.RESIZE)

with WindowManager() as manager:
    manager.layout.add_slot()
    manager.add(window)
