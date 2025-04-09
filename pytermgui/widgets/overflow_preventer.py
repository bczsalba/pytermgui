
from pytermgui import *

def overflow_preventer():
        w = Window.window_height
        c = Container.container_height
        if(c > w):
            raise ValueError("container size is too big and has overflown Window please reconfigure Container size")