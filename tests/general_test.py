#!/usr/bin/env python3
"""
pytermgui/tests/cursor_test.py
------------------------------
author: bczsalba


This file serves to test various terminal functions & context managers.
"""

from time import sleep  # pylint: disable=unused-import
from pytermgui import cursor_at, alt_buffer, cursor_up, clear

with alt_buffer(cursor=False):
    print("if we did everything right, this should disappear")

    with cursor_at((35, 10)) as print_here:
        print_here("and this is the first position")
        print_here("this is the second line")

    with cursor_at((50, 6)) as print_here:
        print_here("this is the second position")
        print_here("this being the line 2:2")

    with cursor_at((70, 16)) as print_here:
        print_here("a third position appears!")
        print_here("what is this, line 3:2? cannot be.")

    # uncomment this if things go ary
    # sleep(0.3)

    cursor_up()
    clear("line")
    print("did it?")
    input()
