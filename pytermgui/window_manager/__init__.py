"""PyTermGUI's WindowManager, Compositor and Window live here.

The window is a subclass of `Container`, and represents a desktop window. It can be
moved, resized and otherwise interacted with.

Compositor is a class specialized at drawing Window objects. It tries to be as efficient
as possible, and follow a given target framerate.

WindowManager is what ties the two together. It manages its list of Windows, transmits
and handles mouse input and more.
"""

from .compositor import Compositor
from .layouts import Layout
from .manager import WindowManager
from .window import Window
