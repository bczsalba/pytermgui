"""
pytermgui.exceptions
--------------------
author: bczsalba


This module stores the custom Exception-s used in this module.
"""


class WidthExceededError(Exception):
    """Raised when an element's width is larger than the screen"""
