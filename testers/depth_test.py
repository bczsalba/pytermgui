#!/usr/bin/env python3
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

from pytermgui import Container,Label,Prompt,set_style,getch,color,bold,get_gradient
from pytermgui.utils import wipe,basic_selection,interactive,height,width

def color_depth(depth,item,do_bold=True):
    c =  color(item,max(236,255-4*depth))
    if do_bold:
        return bold(c)
    return c

def gradient_depth(depth,item):
    colors = get_gradient(accent2)
    index = min(len(colors)-1,depth*2)

    return bold(color(item,colors[index]))

wipe()
accent1,accent2 = interactive.setup()
set_style('container_corner',      lambda depth,item: color_depth(depth,str(depth)))
set_style('container_border',      lambda depth,item: gradient_depth(depth,item))
set_style('label_value',           lambda depth,item: color_depth(depth,f'depth_{depth}'))
set_style('prompt_label',          lambda depth,item: color_depth(depth,f'prompt_{depth}',0))
set_style('container_value',       lambda depth,item: str(depth))

c = Container(width=40)
c._handle_long_element = lambda e: e
c.add_elements(Label('depth'))
c.add_elements(Prompt('prompt'))

d = Container()
d._handle_long_element = lambda e: e
d.add_elements(Label('depth'))
d.add_elements(Prompt('prompt'))

e = Container()
e._handle_long_element = lambda e: e
e.add_elements(Label('depth'))
e.add_elements(Prompt('prompt'))
d.add_elements(e)

ad = Container()
ad._handle_long_element = lambda e: e
ad.add_elements(Label('depth'))
ad.add_elements(Prompt('prompt'))
e.add_elements(ad)

f = Container()
f._handle_long_element = lambda e: e
f.add_elements(Label('depth'))
f.add_elements(Prompt('prompt'))

g = Container()
g._handle_long_element = lambda e: e
g.add_elements(Label('depth'))
g.add_elements(Prompt('prompt'))
f.add_elements(g)

h = Container()
h._handle_long_element = lambda e: e
h.add_elements(Label('depth'))
h.add_elements(Prompt('prompt'))
g.add_elements(h)


c.add_elements(d)
c.add_elements(f)
c.add_elements('pls dont wokr')

c.center()
print(c)

basic_selection(c)
