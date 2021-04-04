from ..input import getch

class keys:
    prev = ["ARROW_UP","CTRL_K","k"]
    next = ["ARROW_DOWN","CTRL_N","j"]
    backwards = ["ARROW_LEFT","CTRL_B","h"]
    forewards = ["ARROW_RIGHT","CTRL_F","l"]

def clr():
    print('\033[2J\033[H')

def basic_selection(obj,break_on_submit=False):
    while True:
        key = getch()

        if key in keys.prev:
            obj.selected_index -= 1

        elif key in keys.next:
            obj.selected_index += 1

        elif key == "ENTER":
            obj.submit()
            if break_on_submit:
                break
        
        elif key in ["ESC","SIGTERM"]:
            clr()
            break

        obj.select()
        print(obj)
