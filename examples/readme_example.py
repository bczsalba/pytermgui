""" pytermgui/examples/readme_example.py
----------------------------
author: bczsalba


Very simple "getting started" file.
Contains code from README.md, but has comments too!
"""

from pytermgui import Container,container_from_dict,getch
from pytermgui.utils import basic_selection

# set up dummy data dictionary
data = {
    "ui__title": "Test data",
    "key": "value",
    "key2": "value2",
    "ui__button": {
        "id": "test-data_button",
        "value": "publish!"
    }
}

# get list of containers from data, split by height
containers = container_from_dict(data,width=40)
c = containers[0]

# select 0th element
c.select()

# center container
c.center()

# clear screen (`os.system('clear')` would also suffice)
print('\033[2J')

# print container
print(c)

# this function can be called for a very basic selection loop, 
# but it is recommended to write your own for most applications.
basic_selection(c)
