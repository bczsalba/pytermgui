from pytermgui import Container,container_from_dict,getch

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


# input loop
while True:
    # get key
    key = getch()

    # go up/down in selection
    if key == "ARROW_UP":
        c.selected_index -= 1
    elif key == "ARROW_DOWN":
        c.selected_index += 1

    # pytermgui captures SIGTERM currently, so you need to handle it yourself
    elif key == "SIGTERM":
        raise KeyboardInterrupt

    # do new selection
    c.select()

    # print
    print(c)
