"""
pytermgui.widgets
-----------------
author: bczsalba


This module provides some widgets to be used in pytermgui.
The basic usage is to create a main Container(), and use
the `+=` operator to append elements to it.
"""

from .base import Widget, Container, Prompt, Label
from .extra import ListView, ColorPicker, InputField, ProgressBar

__all__ = [
    "Widget",
    "Container",
    "Prompt",
    "Label",
    "ListView",
    "ColorPicker",
    "InputField",
    "ProgressBar",
]
