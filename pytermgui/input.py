# taken and edited from https://code.activestate.com/recipes/134892/
# fun note: it was posted 18 years ago and still works!
# originally written by Danny Yoo

import re
import os
import sys
import codecs
import select
from contextlib import contextmanager



def clean_ansi(s,t="ansi"):
    if not type(s) in [str,bytes]:
        raise Exception('Value <'+str(s)+'>\'s type ('+str(type(s))+' is not str or bytes')

    ansi = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    unic = re.compile(r'[^\u0000-\u007F]+')
    no_ansi = ansi.sub('',s)
    # no_unic = unic.sub('',no_ansi)

    
    return no_ansi

def real_length(s):
    return len(clean_ansi(s))


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

    def __init__(self,pos=None,linecap=0,default="",prompt='',xlimit=None,ylimit=None,print_at_start=False):
        # set up instance variables
        self.value = default
        self.cursor = len(self.value)
        self.selected = ''
        self.selected_start = 0
        self.selected_end = 0
        self.prompt = prompt
        self.field_color = '\033[0m'
        self.visual_color = ''
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


    def send(self,key,_do_print=True):
        # delete char before cursor
        if key == "BACKSPACE":
            if self.cursor > 0:#real_length(self.prompt):
                left = self.value[:self.cursor-1]
                right = self.value[self.cursor:]
                self.value = left+right
                self.cursor -= 1

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
    def set_cursor_visible(self,value):
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
    def set_value(self,target,cursor=None,highlight=True,force_cursor=False,do_print=True):
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
        buff = ''
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
    def print(self,return_line=False,flush=True,highlight=True):
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
        highlighter = ('\033[7m' if highlight else '')
        if callable(self.visual_color):
            selected_text = self.visual_color(charUnderCursor)
        else:
            selected_text = self.visual_color + charUnderCursor

        # construct line
        line = self.field_color + self.prompt + left + highlighter + selected_text + '\033[0m' + self.field_color + right + '\033[0m'

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


    def visual(self,start=None,end=None):
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

        highlight = '\033[7m'
        self.selected = selected
        self.selected_start = start
        self.selected_end = end

        if callable(self.visual_color):
            selected_text = self.visual_color(selected)
        else:
            selected_text = self.visual_color + selected

        
        self.wipe()
        line = self.prompt+left+highlight+selected_text+self.field_color+right

        # write to stdout
        x,y = self.pos
        sys.stdout.write(f'\033[{y};{x}H'+line)
        sys.stdout.flush()


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



# clean namespace
getch = _Getch()

# example code
if __name__ == "__main__":
    infield = InputField(default="Welcome!",prompt='> ')
    #infield.print()
    infield.visual(3,3)
    sys.exit()

    while True:
        key = getch()
        # catch ^C signal to exit
        if key == "SIGTERM":
            # re-show cursor (IMPORTANT!)
            infield.set_cursor(True)
            break
        else:
            infield.send(key)
        infield.print()
