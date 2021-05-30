"""
pytermgui.widgets.styles
------------------------
author: bczsalba


This submodule provides the basic style methods for Widgets
"""

from typing import Callable, Union
from ..parser import markup_to_ansi
from ..ansi_interface import background

StyleType = Callable[[int, str], str]
CharType = Union[str, list[str]]

def default_foreground(depth: int, item: str) -> str:
    """Default foreground style"""

    _ = depth
    return item


def default_background(depth: int, item: str) -> str:
    """Default background style"""

    return background(item, 30 + depth)


def overrideable_style(depth: int, item: str) -> str:
    """A style method that is meant to be overwritten,
    to use in optional values."""

    return depth * item


def markup_style(depth: int, item: str) -> str:
    """A style that parses markup `item` into ansi"""
    
    _ = depth
    return markup_to_ansi(item)

def create_markup_style(markup: str) -> StyleType:
    """Create a style that uses a given markup template"""

    function: StyleType = lambda depth, item: (
        markup_to_ansi(markup.format(depth=depth, item=item))
    )

    return function
