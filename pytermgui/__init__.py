from .ui import *
from .input import getch, InputField
from . import utils

color         = Color.color
bold          = Color.bold
italic        = Color.italic
gradient      = Color.gradient
highlight     = Color.highlight
underline     = Color.underline
get_gradient  = Color.get_gradient
strikethrough = Color.strikethrough

# this is added in order to avoid padders hogging memory
padding_label = Label()

from .utils import interactive
