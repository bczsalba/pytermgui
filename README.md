pytermgui
=========

A simple module to display UI in the terminal, as well as to read input.

For now, a good example of use would be [teahaz-client](https://github.com/bczsalba/teahaz-client), but documentation will be coming soon.


getting started
----------------
```py
# version with comments & explanation: examples/readme_example.py

from pytermgui import Container,container_from_dict,getch

data = {
    "ui__title": "Test data",
    "key": "value",
    "key2": "value2",
    "ui__button": {
        "id": "test-data_button",
        "value": "publish!"
    }
}

containers = container_from_dict(data,width=40)
c = containers[0]

c.select()
c.center()
print('\033[2J')
print(c)

# - this can be substituted for:
# from pytermgui.utils import basic_selection
# basic_selection(c)
# - but for anything more advanced than basic use
#   you should define your own method.
while True:
    key = getch()

    if key == "ARROW_UP":
        c.selected_index -= 1

    elif key == "ARROW_DOWN":
        c.selected_index += 1

    elif key == "SIGTERM":
        raise KeyboardInterrupt

    c.select()
    print(c)
```
![readme-example](https://raw.githubusercontent.com/bczsalba/pytermgui/master/img/readme-example.png)

images
--------
### examples/basic_menu.py:
![basic_menu](https://raw.githubusercontent.com/bczsalba/pytermgui/master/img/basic-menu.png)

### examples/project_picker.py:
![project_picker](https://raw.githubusercontent.com/bczsalba/pytermgui/master/img/project-picker.png)

### teahaz menu picker:
![menu_picker](https://raw.githubusercontent.com/bczsalba/pytermgui/master/img/teahaz-menupicker.png)

### teahaz file picker:
![filepicker](https://raw.githubusercontent.com/bczsalba/pytermgui/master/img/teahaz-filemanager.png)
