# taken and edited from https://code.activestate.com/recipes/134892/
# fun note: it was posted 18 years ago and still works!
# originally written by Danny Yoo

import re
import os
import sys
import codecs
import select
from typing import Callable

try:
    import pyperclip as clip
    USE_CLIPBOARD = True
except ImportError:
    USE_CLIPBOARD = False

from .ui import clean_ansi, real_length, Color
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

class InputField:
    """ Example of use at the bottom of the file """

    def __init__(self, pos: list=None, linecap: int=0, default: str="", prompt: str='', xlimit: int=None, ylimit: int=None, print_at_start: bool=None):
        # set up instance variables
        self.value = default
        self.cursor = len(self.value)
        self.selected = ''
        self.selected_start = 0
        self.selected_end = 0
        self.prompt = prompt
        self.empty_cursor_char = ' '

        # TODO
        self.linecap = linecap
        self.xlimit = xlimit
        self.ylimit = ylimit

        # set position as needed
        if pos == None:
            _,tHeight = os.get_terminal_size()
            self.pos = [0,tHeight]
        else:
            self.pos = pos

        # disable cursor
        self.set_cursor_visible(False)

        if print_at_start:
            # print
            self.print()

        self.width = len(self.value)
        self.height = 1
        self._is_selectable = False
        self._strip_pasted_newlines = True

        self.value_style = lambda item: item
        self.highlight_style = lambda item: Color.highlight(item,7)


    def send(self, key:str, _do_print: bool=False):
        # delete char before cursor
        if key == "BACKSPACE":
            if self.cursor > 0:#real_length(self.prompt):
                left = self.value[:self.cursor-1]
                right = self.value[self.cursor:]
                self.value = left+right
                self.cursor -= 1

        elif key == "CTRL_V" and USE_CLIPBOARD:
            left  = self.value[:self.cursor]
            right = self.value[self.cursor:]
            paste = clip.paste()
            if self._strip_pasted_newlines:
                paste = paste.replace('\n','')
            self.value   = left+paste+right
            self.cursor += real_length(paste)

        # move left
        elif key == "ARROW_LEFT":
            self.cursor = max(self.cursor-1,real_length(self.prompt))

        # move right
        elif key == "ARROW_RIGHT":
            self.cursor = min(self.cursor+1,len(self.value))

        # TODO: history navigation, toggleable
        elif key in ["ARROW_DOWN","ARROW_UP"]:
            key = ''

        # TODO
        # elif key == '\n':
            # pass

        else:
            if not (self.xlimit and len(self.value+key) > self.xlimit):
                # add character at cursor
                left = self.value[:self.cursor]
                right = self.value[self.cursor:]
                self.value = left+key+right
                self.cursor += len(key)

        if _do_print:
            self.print()


    # enable/disable (terminal) cursor
    def set_cursor_visible(self, value:bool):
        if value:
            print('\033[?25h')
        else:
            print('\033[?25l')


    # reset self.value
    def clear_value(self):
        self.wipe()
        self.value = ''
        self.cursor = len(self.value)
        self.print()


    # set value, cursor location, pass highlight
    def set_value(self, target:str,cursor: int=None, highlight: bool=True, force_cursor: bool=False, do_print: bool=True):
        # clear space
        self.wipe()

        # set new value
        self.value = target

        # set cursor auto
        if cursor == None or cursor > real_length(self.value)-1 and not force_cursor:
            self.cursor = max(real_length(self.value)-1,0)

        # set cursor manual
        elif not cursor == None:
            self.cursor = cursor

        self.width = real_length(self.value)

        if do_print:
            # print self
            self.print(highlight=highlight)
 

    # clear the space occupied by input currently
    def wipe(self):
        x,y = self.pos
        lines = []
        buff = self.prompt
        for i,c in enumerate(self.value):
            if c == "\n":
                lines.append(buff)
                buff = ''
            else:
                buff += c
        lines.append(buff)

        for i,l in enumerate(lines):
            sys.stdout.write(f'\033[{y-i};{x}H'+(real_length(l)+2)*' ')

        # length = real_length(self.prompt+self.value)+2
        # sys.stdout.write(f'\033[{y};{x}H'+(length)*'a')
        sys.stdout.flush()


    # print self, flush and show highlight if set
    def print(self, return_line: bool=False, flush: bool=True, highlight: bool=True):
        # set up two sides 
        left = self.value[:self.cursor]
        right = self.value[self.cursor+1:]

        # get char under cursor to highlight
        if callable(self.empty_cursor_char):
            char = self.empty_cursor_char(self)
        else:
            char = self.empty_cursor_char

        if self.cursor > len(self.value)-1:
            charUnderCursor = char
        else:
            charUnderCursor = self.value[self.cursor]

        # set highlighter according to highlight param
        if highlight:
            selected_text = self.highlight_style(charUnderCursor)
        else:
            selected_text = charUnderCursor

        # construct line
        line = self.value_style(self.prompt + left) + selected_text + self.value_style(right)

        if return_line:
            return line

        x,y = self.pos

        # clear current
        self.wipe()
        # write to stdout
        sys.stdout.write(f'\033[{y};{x}H'+line)

        # flush if needed
        if flush:
            sys.stdout.flush()


    def visual(self, start: int=None, end: int=None):
        if start > end:
            temp = end
            end = start
            start = temp

        if start == None or start < real_length(self.prompt):
            start = self.cursor
        if end == None or end > len(self.value)-1:
            end = real_length(self.value)-1

        end += 1

        left = self.value[:start]
        selected = self.value[start:end]
        right = self.value[end:]

        self.selected = selected
        self.selected_start = start
        self.selected_end = end

        selected_text = self.highlight_style(selected)

        
        self.wipe()
        line = self.value_style(self.prompt+left) + selected_text + self.value_style(right)

        # write to stdout
        x,y = self.pos
        sys.stdout.write(f'\033[{y};{x}H'+line)
        sys.stdout.flush()

    
    # .ui integration
    def set_style(self, key:str, value:Callable):
        setattr(self,key+'_style',value)

    def submit(self):
        return self.value

    def __repr__(self):
        return self.print(return_line=1)


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
