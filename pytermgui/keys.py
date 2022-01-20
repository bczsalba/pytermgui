"""
Keys file
"""

# common
LF: str = "\x0d"
CR: str = "\x0a"
ENTER: str = "\x0d"
BACKSPACE: str = "\x08"
SUPR: str = ""
SPACE: str = "\x20"
ESC: str = "\x1b"

# CTRL
CTRL_A: str = '\x01'
CTRL_B: str = '\x02'
CTRL_C: str = '\x03'
CTRL_D: str = '\x04'
CTRL_E: str = '\x05'
CTRL_F: str = '\x06'
CTRL_G: str = '\x07'
CTRL_H: str = '\x08'
CTRL_I: str = '\t'
CTRL_J: str = '\n'
CTRL_K: str = '\x0b'
CTRL_L: str = '\x0c'
CTRL_M: str = '\r'
CTRL_N: str = '\x0e'
CTRL_O: str = '\x0f'
CTRL_P: str = '\x10'
CTRL_Q: str = '\x11'
CTRL_R: str = '\x12'
CTRL_S: str = '\x13'
CTRL_T: str = '\x14'
CTRL_U: str = '\x15'
CTRL_V: str = '\x16'
CTRL_W: str = '\x17'
CTRL_X: str = '\x18'
CTRL_Y: str = '\x19'
CTRL_Z: str = '\x1a'

# ALT
ALT_A: str = "\x1b\x61"

# CTRL + ALT
CTRL_ALT_A: str = "\x1b\x01"

# cursors
UP: str = "\x1b\x5b\x41"
DOWN: str = "\x1b\x5b\x42"
LEFT: str = "\x1b\x5b\x44"
RIGHT: str = "\x1b\x5b\x43"

CTRL_ALT_SUPR: str = "\x1b\x5b\x33\x5e"

# other
F1: str = "\x1b\x4f\x50"
F2: str = "\x1b\x4f\x51"
F3: str = "\x1b\x4f\x52"
F4: str = "\x1b\x4f\x53"
F5: str = "\x1b\x4f\x31\x35\x7e"
F6: str = "\x1b\x4f\x31\x37\x7e"
F7: str = "\x1b\x4f\x31\x38\x7e"
F8: str = "\x1b\x4f\x31\x39\x7e"
F9: str = "\x1b\x4f\x32\x30\x7e"
F10: str = "\x1b\x4f\x32\x31\x7e"
F11: str = "\x1b\x4f\x32\x33\x7e"
F12: str = "\x1b\x4f\x32\x34\x7e"

PAGE_UP: str = "\x1b\x5b\x35\x7e"
PAGE_DOWN: str = "\x1b\x5b\x36\x7e"
HOME: str = "\x1b\x5b\x48"
END: str = "\x1b\x5b\x46"

INSERT: str = "\x1b\x5b\x32\x7e"
SUPR: str = "\x1b\x5b\x33\x7e"


ESCAPE_SEQUENCES: list[str] = [
    "\x1b",
    "\x1b\x5b",
    "\x1b\x5b\x31",
    "\x1b\x5b\x32",
    "\x1b\x5b\x33",
    "\x1b\x5b\x35",
    "\x1b\x5b\x36",
    "\x1b\x5b\x31\x35",
    "\x1b\x5b\x31\x36",
    "\x1b\x5b\x31\x37",
    "\x1b\x5b\x31\x38",
    "\x1b\x5b\x31\x39",
    "\x1b\x5b\x32\x30",
    "\x1b\x5b\x32\x31",
    "\x1b\x5b\x32\x32",
    "\x1b\x5b\x32\x33",
    "\x1b\x5b\x32\x34",
    "\x1b\x4f",
    "\x1b\x1b",
    "\x1b\x1b\x5b",
    "\x1b\x1b\x5b\x32",
    "\x1b\x1b\x5b\x33",
]