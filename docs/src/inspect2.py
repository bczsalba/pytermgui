from pytermgui import Overflow, WindowManager
from pytermgui.cmd import InspectorWindow, _configure_widgets, _create_aliases

_create_aliases()
_configure_widgets()

termage.resize(100, 67)
window = InspectorWindow(overflow=Overflow.RESIZE)
window.get_lines()

with WindowManager() as manager:
    manager.layout.add_slot()
    manager.add(window)

    # This is a hack to get around InputField cursor position starting near the middle;
    # We draw once, then the second draw done by Termage will be correct.
    manager.compositor.draw()
