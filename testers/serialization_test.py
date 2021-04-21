#!/usr/bin/env python3
"""
pytermgui/testers/depth_test.py
-------------------------------
author: bczsalba


Simple script to automatically check if various load and dump methods result
in the same data.
"""

import pytermgui
import sys, os, json

# files are read()-d, so we need to seek to the beginning again 
print('checking load methods: ',end='',flush=True)
with open(os.path.join(os.path.dirname(__file__),'static/serialized.json'),'r') as f:
    load = pytermgui.load(f)
    f.seek(0)
    data = json.load(f)
    f.seek(0)
    loadd = pytermgui.loadd(data.copy())
    loads = pytermgui.loads(json.dumps(data))

if not str(load) == str(loadd) == str(loads):
    # comment this to have a visual check
    raise pytermgui.LoadError('Loaded objects are not the same!')

    for o in [load,loadd,loads]:
        pytermgui.wipe()
        print(o)
        pytermgui.getch()

    sys.exit(1)

print('done!')


print('checking dump methods: ',end='',flush=True)
with open(os.path.join(os.path.dirname(__file__),'_dump.json'),'w+') as f:
    pytermgui.dump(load,f)
    f.seek(0)
    dump = f.read()
    dumps = pytermgui.dumps(load)


if not dump == dumps:
    # comment this to have a visual check
    raise pytermgui.DumpError('Dumped objects are not the same!')

    print(pytermgui.loads(dumps))
    pytermgui.getch()

    print(pytermgui.loads(dump))
    pytermgui.getch()


print('done!')
print('Tests successful!\n')

print('cleaning up... ',end='',flush=True)
os.remove(os.path.join(os.path.dirname(__file__),'_dump.json'))
print('done!\n')

print('Serialization tests completed with no errors!')
