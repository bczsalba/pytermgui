#!/usr/bin/env python3.9
"""
pytermgui/testers/operators_test.py
-----------------------------------
author: bczsalba


Tester file for + and += operators behaving correctly

Rules:
    expression               evaluated to
    ----------               ------------
    e + e                =>  Container().add_elements([e,e])
    container += e + e   =>  container.add_elements([e,e])
    container += [e,e]   =>  container._add_element(Container()->add_elements([e,e]))

    BaseElement + <str>  =>  BaseElement + Label(value=<str>)
    BaseElement + <list> =>  BaseElement + Prompt(options=<list>)
"""

from pytermgui import Label, Prompt, Container, wipe, padding_label, styles
from pytermgui.utils import basic_selection
styles.draculite()
wipe()

# create root container
a = Container()
a += Label("main_container")

# create first level container
d  = Label('inner_one') + Prompt('prompt',value='value')
d += Prompt(options=['option1','option2'])

# create second level container
c  =  ( Label('inner_two') + Prompt('prompt_two',value='value_two'))
c += Label('same level') + Prompt(options=list(range(20 )))

k = c[-1]
c += Label('sub-level:') + [ Label('list') + Prompt('list',value='list') ]

a += d
a += padding_label

a += c
a += padding_label

a += [Label('is this a container?'),Prompt('i damn hope!')]

a += Prompt('main_prompt',padding=2,value='end of file')

a.center()
basic_selection(a)
