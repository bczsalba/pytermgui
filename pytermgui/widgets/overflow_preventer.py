
import pytermgui as ptg


def overflow_preventer(window_height, container_height):

        if(container_height > window_height):
            raise ValueError("container size is too big and has overflown Window please reconfigure Container size")