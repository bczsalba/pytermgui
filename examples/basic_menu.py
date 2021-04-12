"""
pytermgui/examples/readme.py
----------------------------
author: bczsalba


Slightly more involved file for creating a basic menu.
Uses minimal styling
Contains code from README.md, but has comments too!
"""

from pytermgui import Container,container_from_dict,getch,set_style
from pytermgui import color,bold,highlight,gradient
from pytermgui.utils import basic_selection as basic_selection

# set up dummy data
data = {
    "ui__title": "Test data",
    "ui__padding0": 0,
    "key": "value",
    "key2": "longer value",
    "ui__padding1": 0,
    "ui__prompt": ["choice1","choice2"],
    "ui__padding2": 0,
    "ui__button": {
      "id": "test-data_button",
      "value": "publish!"
    }
}

# set styles
set_style('container_title',lambda depth,item: bold(color(item,210)))
set_style('container_label',lambda depth,item: color(item,248))
set_style('container_value',lambda depth,item: color(item,72))
set_style('container_border',lambda depth,item: bold(color(item,60)))
set_style('prompt_short_highlight',lambda depth,item: highlight(item,72))
set_style('prompt_long_highlight',lambda depth,item: highlight(item,72))
set_style('prompt_delimiter_chars',lambda: ['< ',' >'])

# clear screen
print('\033[2J')

# create container list, split by height of screen
containers = container_from_dict(data,width=40)
c = containers[0]

# set up basics
c.center()
c.select()
print(c)

# this function can be called for a very basic selection loop, 
# but it is recommended to write your own for most applications.
basic_selection(c)
