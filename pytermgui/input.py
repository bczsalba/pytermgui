"""
pytermgui.input
---------------
author: bczsalba


File providing the getch() function to easily read character inputs.

TODO: 
    - windows support for CTRL_ keys

credits: 
    - original getch implementation: Danny Yoo (https://code.activestate.com/recipes/134892)
    - modern additions & idea:       kcsaff (https://github.com/kcsaff/getkey)
"""


import re
import os
import sys
import codecs
import select
from typing import Callable

from contextlib import contextmanager




# this needs to be here in order to have arrow keys registered
# from https://github.com/kcsaff/getkey
class OSReadWrapper(object):
    """Wrap os.read binary input with encoding in standard stream interface.
    We need this since os.read works more consistently on unix, but only
    returns byte strings.  Since the user might be typing on an international
    keyboard or pasting unicode, we need to decode that.  Fortunately
    python's stdin has the fileno & encoding attached to it, so we can
    just use that.
    """
    def __init__(self, stream, encoding=None):
        """Construct os.read wrapper.
        Arguments:
            stream (file object): File object to read.
            encoding (str): Encoding to use (gets from stream by default)
        """
        self.__stream = stream
        self.__fd = stream.fileno()
        self.encoding = encoding or stream.encoding
        self.__decoder = codecs.getincrementaldecoder(self.encoding)()

    def fileno(self):
        return self.__fd

    @property
    def buffer(self):
        return self.__stream.buffer

    def read(self, chars):
        buffer = ''
        while len(buffer) < chars:
            buffer += self.__decoder.decode(os.read(self.__fd, 1))
        return buffer

class _Getch:
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()
        
        self.keycodes = {
            # SIGNALS: not captured currently
            "\x03": "SIGTERM",
            "\x1a": "SIGHUP",
            "\x1c": "SIGQUIT",

            # CONTROL KEYS
            "\x17" : "CTRL_W",
            "\x05" : "CTRL_E",
            "\x12" : "CTRL_R",
            "\x14" : "CTRL_T",
            "\x15" : "CTRL_U",
            "\x10" : "CTRL_P",
            "\x1d" : "CTRL_]",
            "\x01" : "CTRL_A",
            "\x04" : "CTRL_D",
            "\x06" : "CTRL_F",
            "\x07" : "CTRL_G",
            "\x08" : "CTRL_H",
            "\x0b" : "CTRL_K",
            "\x0c" : "CTRL_L",
            "\x18" : "CTRL_X",
            "\x16" : "CTRL_V",
            "\x02" : "CTRL_B",
            "\x0e" : "CTRL_N",
            "\x1f" : "CTRL_/",

            # TEXT EDITING
            "\x7f": "BACKSPACE",
            "\x1b": "ESC",
            "\n": "ENTER",
            "\r": "ENTER",
            "\t": "TAB",

            # MOVEMENT
            "\x1b[A": "ARROW_UP",
            "\x1bOA": "ARROW_UP",
            "\x1b[B": "ARROW_DOWN",
            "\x1bOB": "ARROW_DOWN",
            "\x1b[C": "ARROW_RIGHT",
            "\x1bOC": "ARROW_RIGHT",
            "\x1b[D": "ARROW_LEFT",
            "\x1bOD": "ARROW_LEFT",
        }
        
    def __call__(self):
        key = self.impl()

        # return human-readable name if found
        if key in self.keycodes.keys():
            return self.keycodes[key]
        else:
            return key

class _GetchUnix:
    def __init__(self):
        global tty,termios
        import tty,termios

        self.stream = OSReadWrapper(sys.stdin)

    @contextmanager
    def context(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        try:
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def get_chars(self):
        with self.context():
            yield self.stream.read(1)

            while select.select([sys.stdin,], [], [], 0.0)[0]:
                yield self.stream.read(1)

    def __call__(self):
        buff = ''
        try:
            for c in self.get_chars():
                buff += c
        except KeyboardInterrupt:
            return '\x03'

        return buff

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt

        return msvcrt.wgetch()


getch = _Getch()
