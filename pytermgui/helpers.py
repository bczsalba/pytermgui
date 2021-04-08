"""
pytermgui.helpers
-----------------


File providing mostly internally used helper methods.
"""

from . import Regex
from typing import AnyStr

def clean_ansi(s: AnyStr):
    """ Remove ansi characters from `s`, and replace all unicode characters with '**' """

    if not type(s) in [str,bytes]:
        raise Exception('Value <'+str(s)+'>\'s type ('+str(type(s))+' is not str or bytes')

    no_ansi = Regex.ansi.sub('',s)
    no_unic = Regex.unic.sub('**',no_ansi)

    return no_unic

def real_length(s: AnyStr):
    """ Return real (not containing modifier sequences) length of `s`, using `clean_ansi` """

    return len(clean_ansi(s))

def break_line(_inline: AnyStr, _len: int, _pad: int=0, _separator: str=' ', do_subdivision: bool=True):
    """ 
    Break `_inline` to fit into `_len`, primarily splitting by `_separator`.

    TODO: add checks for ansi modifiers, so that if a line has a style
          it continues regardless of how many linebreaks happen, until
          it's escaped.
    """

    if _len == None:
        return [_inline]
    
    if _inline.count('\n'):
        lines = _inline.split('\n')
        newlines = []
        for l in lines:
            newlines += break_line(l,_len,_pad,_separator,do_subdivision)

        return newlines


    # check if line is over length provided
    elif real_length(_inline) > _len:
        clean = clean_ansi(_inline)
        current = ''
        control = ''
        lines = []
        pad = lambda l: (_pad*' ' if len(l) else '')

        pattern    = f'[{_separator}]'
        cleansplit = clean.split(_separator)
        insplit    = _inline.split(_separator)

        for i,(clen,real) in enumerate(zip(cleansplit,insplit)):
            # dont add separator if no current
            sep = (_separator if len(current) else "") 

            # add string to line if not too long
            if len(pad(lines)+control+_separator+clen) <= _len:
                current += sep + real
                control += sep + clen

            # add current to lines
            elif len(current):
                lines.append(pad(lines)+current)
                current = real
                control = clen

        # add leftover values
        if len(current):
            lines.append(pad(lines)+current)

        if not len(lines):
            lines = insplit


    # return original line in array
    else:
        lines = _inline.split('\n')

    if do_subdivision:
        newlines = []
        # TODO: make this work with colored text
        for i,l in enumerate(lines):
            if real_length(l) >= _len:
                clean = clean_ansi(l)

                buff = ''
                for charindex,c in enumerate(clean):
                    buff += c
                    if len(buff) >= _len:
                        newlines.append(buff)
                        buff = ''

                if len(buff):
                    newlines.append(buff)

            else:
                newlines.append(l)
    else:
        newlines = lines

    return newlines
