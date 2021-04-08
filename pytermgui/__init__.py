"""
pytermgui
---------
author: bczsalba


Python framework for terminal-based GUI applications.
"""


import re

class Color:
    def bold(s):
        return '\033[1m'+str(s)+'\033[0m'

    def italic(s):
        return '\033[3m'+str(s)+'\033[0m'

    def underline(s):
        return '\033[4m'+str(s)+'\033[0m'
    
    def strikethrough(s):
        return '\033[9m'+str(s)+'\033[0m'

    def highlight(s,fg="1"):
        if s.startswith('\033['):
            return '\033[7m'+s

        if not isinstance(fg,int) and not fg.isdigit():
            return '\033[7m'+fg

        return '\033[7m'+ (Color.color(clean_ansi(s),fg) if fg else s)

    def color(s,col,reset=True):
        if isinstance(col,list):
            raise Exception('color argument `col` has to be of type int or string')

        return f'\033[{DEFAULT_COLOR_PREFIX};{col}m'+str(s)+('\033[0m' if reset else '')

    # get 5 length gradient including `include`
    def get_gradient(include,direction='vertical'):
        # do rainbow gradient
        if include == 'rainbow':
            return ['124','208','226','82','21','57','93']
        elif isinstance(include,str) and not include.isdigit():
            raise Exception('bad include value '+include+'.')

        c = int(include)
        colors = []

        # go vertically in color chart
        if direction == 'vertical':
            # get starting value
            while c > 36:
                c -= 36

            # get and add values
            while c <= 231-36:
                c += 36
                colors.append(str(c))

        # go horizontally in color chart
        else:
            # get starting value
            if c < 16:
                c = 16

            while c > 16 and not (c-16) % 6 == 0:
                print(c-16)
                c -= 1

            # get and add values
            for _ in range(5):
                c += 1
                colors.append(str(c))

        return colors

    def gradient(text,color,layer='fg'):
        colors = []

        if isinstance(color,list):
            values = color
        else:
            values = Color.get_gradient(color)

        # get ratio between text and value lengths
        ratio = max(1,len(text)/len(values))
        if not isinstance(ratio,int) and not ratio.is_integer():
            ratio = int(ratio)+1
        else:
            ratio = int(ratio)

        # add color `ratio` times
        for v in values:
            for _ in range(ratio):
                colors.append(v)

        # add colored text
        out = ''
        for char,col in zip(clean_ansi(text),colors):
            if layer == 'bg':
                out += '\033[7m'
            out += Color.color(char,col,reset=False)
        out += '\033[00;00m'
        return out

class Regex:
    ansi   = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    unic   = re.compile(r'[^\u0000-\u007F]')
    emoji  = re.compile(r':[a-z_]+:')
    dunder = re.compile(r'__[a-z_]+__')

color         = Color.color
bold          = Color.bold
italic        = Color.italic
gradient      = Color.gradient
highlight     = Color.highlight
underline     = Color.underline
get_gradient  = Color.get_gradient
strikethrough = Color.strikethrough

from .ui import *
# this is added in order to avoid padders hogging memory
padding_label = Label()

from .helpers import *
from .input import getch
from .utils import interactive
from . import utils
