"""
pytermgui
---------
author: bczsalba


Python framework for terminal-based GUI applications.
"""
__version__ = "0.0.8"


import re


class Color:
    """ Class containing methods for coloring """

    def bold(s):
        """ Return bold version of `s` """

        return "\033[1m" + str(s) + "\033[0m"

    def italic(s):
        """ Return italic version of `s` """

        return "\033[3m" + str(s) + "\033[0m"

    def underline(s):
        """ Return underlined version of `s` """

        return "\033[4m" + str(s) + "\033[0m"

    def strikethrough(s):
        """ Return strikethrough version of `s` """

        return "\033[9m" + str(s) + "\033[0m"

    def highlight(s, fg="1"):
        """ Return version of `s` highlighted with color(`fg`) """

        if s.startswith("\033["):
            return "\033[7m" + s

        if not isinstance(fg, int) and not fg.isdigit():
            return "\033[7m" + fg

        return "\033[7m" + (Color.color(clean_ansi(s), fg) if fg else s)

    def color(s, col, reset=True):
        """ Return `s` colored with `col`, add reset character if reset """

        if isinstance(col, list):
            raise Exception("color argument `col` has to be of type int or string")

        return (
            f"\033[{DEFAULT_COLOR_PREFIX};{col}m"
            + str(s)
            + ("\033[0m" if reset else "")
        )

    def get_gradient(include, direction="vertical"):
        """ Return 5 length gradient including color `include`, traversing colors in `direction` """

        # do rainbow gradient
        if include == "rainbow":
            return ["124", "208", "226", "82", "21", "57", "93"]
        elif isinstance(include, str) and not include.isdigit():
            raise Exception("bad include value " + include + ".")

        c = int(include)
        colors = []

        # go vertically in color chart
        if direction == "vertical":
            # get starting value
            while c > 36:
                c -= 36

            # get and add values
            while c <= 231 - 36:
                c += 36
                colors.append(str(c))

        # go horizontally in color chart
        else:
            # get starting value
            if c < 16:
                c = 16

            while c > 16 and not (c - 16) % 6 == 0:
                print(c - 16)
                c -= 1

            # get and add values
            for _ in range(5):
                c += 1
                colors.append(str(c))

        return colors

    def gradient(text, color, layer="fg"):
        """
        Apply colors in color is isinstance(color,list) else apply get_gradient(`color`) on text, coloring layer fg/bg
        """

        colors = []

        if isinstance(color, list):
            values = color
        else:
            values = Color.get_gradient(color)

        # get ratio between text and value lengths
        ratio = max(1, len(text) / len(values))
        if not isinstance(ratio, int) and not ratio.is_integer():
            ratio = int(ratio) + 1
        else:
            ratio = int(ratio)

        # add color `ratio` times
        for v in values:
            for _ in range(ratio):
                colors.append(v)

        # add colored text
        out = ""
        for char, col in zip(clean_ansi(text), colors):
            if layer == "bg":
                out += "\033[7m"
            out += Color.color(char, col, reset=False)
        out += "\033[00;00m"
        return out


class Regex:
    ansi = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    unic = re.compile(r"[^\u0000-\u007F]")
    emoji = re.compile(r":[a-z_]+:")
    dunder = re.compile(r"__[a-z_]+__")


color = Color.color
bold = Color.bold
italic = Color.italic
gradient = Color.gradient
highlight = Color.highlight
underline = Color.underline
get_gradient = Color.get_gradient
strikethrough = Color.strikethrough

from .ui import *

# this is added in order to avoid padders hogging memory
padding_label = Label()

from .helpers import *
from .input import getch
from .utils import interactive
from . import utils, styles
import cmd
