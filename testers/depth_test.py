#!/usr/bin/env python3.9
"""
pytermgui/testers/depth_test.py
-------------------------------
author: bczsalba


Simple script to visually test if nested Containers
keep and update element depths properly.

BUG:
    Depth 4 selection doesn't work. Selectables has the right length,
    and you can manually select the element just fine, but it won't 
    print in the main object. :(
"""

from pytermgui import Container,Label,Prompt,set_style,getch,color,bold,get_gradient,styles
from pytermgui.utils import wipe,basic_selection,interactive,height,width

def color_depth(depth,item,do_bold=True):
    c =  color(item,max(0,236+4*depth))
    if do_bold:
        return bold(c)
    return c

def gradient_depth(depth,item):
    colors = get_gradient(accent2)
    index = min(len(colors)-1,depth*2)

    return bold(color(item,colors[index]))

def create():
    return ( Label('depth') + Prompt('prompt') )


# wipe()

styles.random()
accent1,accent2 = styles.random()

set_style('container_corner',       lambda depth,item: color_depth(depth,str(depth)))
set_style('container_border',       lambda depth,item: gradient_depth(depth,item))
set_style('label_value',            lambda depth,item: color_depth(depth,f'depth_{depth}'))
set_style('prompt_label',           lambda depth,item: color_depth(depth,f'prompt_{depth}',0))
set_style('prompt_delimiter_chars', lambda: None)
set_style('container_value',        lambda depth,item: str(depth))

c  = create()
d  = create()

e  = create()
d.add_elements(e)

ad = create()
e.add_elements(ad)

f  = create()

g  = create()
f.add_elements(g)

h = create()
g.add_elements(h)

c.add_elements(d)
c.add_elements(f)

c.center()
print(c)

# basic_selection(c)
import pytermgui
with open('testers/static/serialized.json','w') as f:
    pytermgui.dump(c,f)
