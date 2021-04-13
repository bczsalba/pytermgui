#!/usr/bin/env python3
"""
pytermgui/testers/operators_test.py
-----------------------------------
author: bczsalba


Tester file for + and += operators behaving correctly
"""

from pytermgui import Label, Prompt, Container, wipe, padding_label
from pytermgui.utils import basic_selection
from pytermgui.utils.interactive import setup


setup()
a = Container()
a += Label("main_container")

d = Label('inner_one') + Prompt('prompt',value='value')
d += Prompt(options=['option1','option2'])

c =  ( Label('inner_two') + Prompt('prompt_two',value='value_two'))
c += ( Label('inner_inner') + Prompt('inner_prompt',value='inner_value') )

a += d
a += padding_label

a += c
a += padding_label

a += Prompt('main_prompt',padding=2,value='end of file')

a.center()
basic_selection(a)
