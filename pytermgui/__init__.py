"""
pytermgui
---------
author: bczsalba


A simple and robust terminal UI library, written in Python.
"""

from .input import getch
from .classes import BaseElement, Container
from .context_managers import alt_buffer, cursor_at

from .ansi_interface import (
    get_screen_size,
    width,
    height,
    save_screen,
    restore_screen,
    start_alt_buffer,
    end_alt_buffer,
    clear,
    hide_cursor,
    show_cursor,
    save_cursor,
    restore_cursor,
    report_cursor,
    move_cursor,
    cursor_up,
    cursor_down,
    cursor_right,
    cursor_left,
    cursor_next_line,
    cursor_prev_line,
    cursor_column,
    cursor_home,
    print_to,
)
