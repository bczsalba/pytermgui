from pytermgui import Container,container_from_dict,getch,set_style
from pytermgui import color,bold,highlight,gradient

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
set_style('container_title',lambda item: bold(color(item,210)))
set_style('container_label',lambda item: color(item,248))
set_style('container_value',lambda item: color(item,72))
set_style('container_border',lambda item: bold(color(item,60)))
set_style('prompt_short_highlight',lambda item: highlight(item,72))
set_style('prompt_long_highlight',lambda item: highlight(item,72))
set_style('prompt_delimiter_style',lambda: ['< ',' >'])

# clear screen
print('\033[2J')

# create container list, split by height of screen
containers = container_from_dict(data,width=40)
c = containers[0]

# set up basics
c.center()
c.select()
print(c)

while True:
    key = getch()

    if key == "ARROW_UP":
        c.selected_index -= 1
    elif key == "ARROW_DOWN":
        c.selected_index += 1

    # SIGTERM is current captured, so you need to handle it.
    elif key == "SIGTERM":
        import sys
        sys.exit(0)

    c.select()
    print(c)
