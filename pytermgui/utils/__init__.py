"""
pytermgui.utils
---------------
author: bczsalba


A subpackage providing simple utilities to pytermgui.
"""

from ..input import getch
from ..ui import InputField, Container, Prompt, Label, wipe
import os


class keys:
    prev = ["ARROW_UP","CTRL_P","k"]
    next = ["ARROW_DOWN","CTRL_N","j"]
    back = ["ARROW_LEFT","CTRL_B","h"]
    fore = ["ARROW_RIGHT","CTRL_F","l"]

def hide_cursor(value: bool=True):
    InputField.set_cursor_visible('',not value)

def basic_selection(obj,break_on_submit=False):
    obj.select()
    print(obj)
    while True:
        key = getch()

        if key in keys.prev:
            obj.selected_index -= 1

        elif key in keys.next:
            obj.selected_index += 1

        elif key == "ENTER":
            obj.submit()
            if break_on_submit:
                wipe()
                break
        
        elif key in ["ESC","SIGTERM"]:
            wipe()
            break

        obj.select()
        print(obj)

def width():
    return os.get_terminal_size()[0]

def height():
    return os.get_terminal_size()[1]

def size():
    return os.get_terminal_size()
