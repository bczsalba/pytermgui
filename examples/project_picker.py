#!/usr/bin/env python3
"""
pytermgui/examples/project_picker.py
------------------------------------

Program that reads a list of `projects` from 
`CONFIG_LOCATION`, and presents you with a picker
to select from them. 

The config file is generated if not found, and allows for
simple styling.

KEYS:
    - SPACE: open directory in new bash shell
    - ENTER: open directory/file in `EDITOR`
    - gg   : go to top
    - G    : go to bottom
"""

# constants
CONFIG_LOCATION = "/Users/plum/.config/vim/"
EDITOR = "vim"

# --------------------------------------------

from pytermgui import color,bold,italic,underline,set_style,highlight,get_gradient
from pytermgui import Container,Prompt,Label,InputField
from pytermgui import container_from_dict,getch
import os,sys

# get config file
sys.path.insert(0,CONFIG_LOCATION)

try: from launcher_conf import projects,styles
except ImportError:
    with open(os.path.join(CONFIG_LOCATION,'launcher_conf.py'),'w') as f:
        f.write('projects = []\n\n')
        f.write('styles = {\n')
        f.write('    "title_text": "projects",\n')
        f.write('    "title": "225",\n')
        f.write('    "prompt": "249",\n')
        f.write('    "highlight": "141",\n')
        f.write('    "border": "60",\n')
        f.write('    "corners": "xxxx"\n')
        f.write('}')
        print('config file created at',CONFIG_LOCATION+'launcher_conf.py!')
        sys.exit(0)
projects.sort()


# set basic styles
set_style('container_border',lambda depth,item: bold(color(item,get_gradient(styles.get('border'))[depth])))
set_style('prompt_long_highlight',lambda item: highlight(item,styles.get('highlight')))


# create container
c = Container(width=50)

# overwrite long elment handler
c._handle_long_element = lambda e: ''

# set corners to x-es
if styles.get('corners'):
    for i in range(len(styles['corners'])):
        c.set_corner(i,styles['corners'][i])

# create and add title
title = Label(value=styles.get('title_text'),justify='left')
title.set_style('value',lambda item: bold(color(item,styles.get('title'))))
line = Label('--------',justify='left')
line.set_style('value', title.value_style)

c.add_elements([title,line])

# go through projects
for p in projects:
    value = os.path.split(p)[1]
    # create Prompt
    prompt = Prompt(label=value,padding=2)
    # set value to be referenced on enter
    prompt.path = p
    # set delimiters to be None
    prompt.set_style('delimiter',lambda: None)
    prompt.set_style('label',lambda item: color(item,styles.get('prompt')))
    # add to container
    c.add_elements(prompt)

# clear the screen, hide cursor
print('\033[2J')
InputField.set_cursor_visible('',False)

c.center()
c.select()
print(c)

while True:
    key = getch()

    # navigating
    if key in ["ARROW_UP","k"]:
        c.selected_index -= 1
    elif key in ["ARROW_DOWN","j"]:
        c.selected_index += 1
    
    # close menu
    elif key in ['SIGTERM','q','CTRL_D']:
        # clear screen
        os.system('clear')
        # show cursor
        InputField.set_cursor_visible('',True)
        # exit
        sys.exit(0)

    # opening the selected elements 
    elif key in ["ENTER"," "]:
        obj,sub_index,total_index = c.selected

        # open a file
        if os.path.isfile(obj.path):
            path,file = os.path.split(obj.path)

            if key == "ENTER":
                os.system(f'cd "{path}"; {EDITOR} "{file}"')
            else:
                os.chdir(path)
                InputField.set_cursor_visible('',True)
                os.system('bash')


        # open a dir
        else:
            os.system(f'cd "{obj.path}"')
            
            if key == "ENTER":
                os.system(f'{EDITOR} "{obj.path}"')
            else:
                os.chdir(obj.path)
                InputField.set_cursor_visible('',True)
                os.system('bash')

        os.system('clear')
        InputField.set_cursor_visible('',False)

    elif key == " ":
        obj,sub_index,total_index = c.selected
        

    # select the bottom
    elif key == "G":
        c.selected_index = len(c.selectables)-1

    # select the top
    elif key == "g":
        key = getch()
        if key == "g":
            c.selected_index = 0

    c.select()
    print(c)
