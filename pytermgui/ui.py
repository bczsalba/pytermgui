import sys,os,time,re


class Regex:
    ansi   = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    unic   = re.compile(r'[^\u0000-\u007F]')
    emoji  = re.compile(r':[a-z_]+:')
    dunder = re.compile(r'__[a-z_]+__')

# HELPERS #
def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def dbg(*args,**kwargs):
    print(*args,**kwargs)

def set_debugger(fun):
    globals()['dbg'] = fun

def set_style(key,value):
    key = key.upper()

    if key in globals():
        globals()[key] = value
    else:
        globals()[key+'_STYLE'] = value

    return key+'_STYLE'

def clean_ansi(s):
    if not type(s) in [str,bytes]:
        raise Exception('Value <'+str(s)+'>\'s type ('+str(type(s))+' is not str or bytes')

    no_ansi = Regex.ansi.sub('',s)
    no_unic = Regex.unic.sub('**',no_ansi)

    return no_unic

def real_length(s):
    return len(clean_ansi(s))

def break_line(_inline,_len,_pad=0,_separator=' ',do_subdivision=True):
    # TODO: add checks for ansi modifiers, so that if a line has a style
    #       it continues regardless of how many linebreaks happen, until
    #       it's escaped.

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



def set_element_id(element,element_id):
    element.id = element_id
    ELEMENT_IDS[element_id] = element

    # set given attributes 
    if not ELEMENT_ATTRIBUTES.get(element_id) == None:
        for attribute,value in ELEMENT_ATTRIBUTES[element_id].items():
            setattr(element,attribute,value)

# set attributes to be applied to all elements matching id
def set_attribute_for_id(element_id,key,value):
    if element_id in ELEMENT_ATTRIBUTES.keys():
        ELEMENT_ATTRIBUTES[element_id][key] = value
    else:
        ELEMENT_ATTRIBUTES[element_id] = { key: value } 

    obj = get_object_by_id(element_id)
    if obj:
        setattr(obj,key,value)
    
def get_object_by_id(key):
    return ELEMENT_IDS.get(key)

def set_listener(event,func):
    globals()['event__'+event] = func


# EXAMPLES #

# generate list of containers from dict
# padding sets how much text should be indented under titles
#
# returns a list of Container objects, len() > 1 if the 
# container height wouldn't fit the screen
def container_from_dict(dic,padding=4,_prompts_selectable=True,**kwargs):
    dic_c = Container(**kwargs)

    dicts = [dic_c]
    reverse_items = False
    handler = None
    current_padding = 2
    prompt_options = None
    datafile = None
    element_id = None


    for i,(key,item) in enumerate(dic.items()):
        if key.startswith('ui__'):        
            # GENERATOR OPTIONS
            ## set datafile for all objects
            if key == "ui__file":
                datafile = item

            ## read titles into labels
            elif "_title" in key:
                # get next title element
                for next_title,k in enumerate(list(dic.keys())[i+1:]):
                    if k.startswith('ui__title') and k[-1].isdigit():
                        break

                l = Label(value=item,justify="left")

                if key.startswith('ui__title'):
                    l.set_style('value',CONTAINER_TITLE_STYLE)

                elif key.startswith('ui__success_title'):
                    l.set_style('value',CONTAINER_SUCCESS_STYLE)

                elif key.startswith('ui__error_title'):
                    l.set_style('value',CONTAINER_ERROR_STYLE)

                # set id
                if not element_id == None:
                    set_element_id(l,element_id)
                    element_id = None

                height_with_segment = dicts[-1].real_height + next_title*(1+dicts[-1].padding)+5
                
                if height_with_segment > HEIGHT-5:
                    dicts.append(Container(**kwargs))
                    dicts[-1].add_elements(l)
                    continue

                
                # only pad if not the first element
                if not i == 0 and not list(dic.keys())[i-1] == "ui__file":
                    pad = Label()
                    dicts[-1].add_elements(pad)

                # add label to container
                dicts[-1].add_elements(l)

                # set new padding value
                current_padding = padding

            ## set options for next prompt
            elif key.startswith("ui__prompt_options"):
                prompt_options = item

            ## reverse keys and values
            elif key == "ui__reverse_items":
                reverse_items = True

            ## set next element id
            elif key.startswith("ui__id"):
                element_id = item


            # ELEMENT SHORTHANDS
            ## create prompt with options `item`
            elif key.startswith("ui__prompt"):
                options = item
                p = Prompt(options=options)
                p.set_style('value',CONTAINER_VALUE_STYLE)
                
                if element_id:
                    set_element_id(p,element_id)
                    element_id = None

                dicts[-1].add_elements(p)
 
            ## create padder
            elif key.startswith("ui__padding"):
                p = Label()

                if element_id:
                    set_element_id(p,element_id)
                    element_id = None

                dicts[-1].add_elements(p)

            elif key.startswith("ui__button"):
                button = Prompt(options=[item.get('value')])
                button.set_style('value',CONTAINER_VALUE_STYLE)

                set_element_id(button,item.get('id'))

                if not hasattr(button,'handler'):
                    button.handler = lambda *args: None

                dicts[-1].add_elements(button)
            
            elif key.startswith('ui__label'):
                justify = item.get('justify')
                value = item.get('value')
                padding = item.get('padding')

                if element_id:
                    set_element_id(p,element_id)
                    element_id = None

                label = Label(value=value,justify=justify,padding=padding)
                dicts[-1].add_elements(label)

        else:
            # reverse meanings of key & item
            if reverse_items:
                temp = key
                key = item
                item = temp

            # set real value (not str())
            real_value = item

            # ignore empty dicts
            if isinstance(item,dict):
                length = len(item.keys())
                if length == 0:
                    continue
                else:
                    #item = "bl!"
                    item = "->"
                    delim = ''
            else:
                delim = None
            

            # create, add prompt
            p = Prompt(real_label=str(key),label=str(key),value=str(item),padding=current_padding)
            p.__ui_options = prompt_options
            prompt_options = None
            p.set_style('label',CONTAINER_LABEL_STYLE)
            p.set_style('value',CONTAINER_VALUE_STYLE)
            p.real_value = real_value
            p._is_selectable = _prompts_selectable

            if element_id:
                set_element_id(p,element_id)
                element_id = None

            if not delim == None:
                p.delimiter_style = lambda: ['   ','{}']
                p.set_style('value',CONTAINER_LABEL_STYLE)


            # this array keeps track of path within a dictionary
            p.__ui_keys = []

            # add prompt to dict
            if dicts[-1].height + p.height > HEIGHT-5:
                dicts.append(Container(**kwargs))


            dicts[-1].add_elements(p)


    do_tabline = len(dicts) > 1
    for i,d in enumerate(dicts):
        d.__ui_keys = []
        if not datafile == None:
            for e in d.elements:
                e.file = datafile
            d.file = datafile

        if do_tabline:
            tabline = Prompt(options=[n for n in range(len(dicts))])
            tabline.set_style('short_highlight',TABBAR_HIGHLIGHT_STYLE)
            tabline.select(i)
            tabline._is_selectable = False
            d.add_elements([Label(),tabline])

    return dicts




# COLORS #
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




# EVENTS #
def event__window_size_changed(caller,new,old):
    pass


# CLASSES #
class Container:
    """
    Object that contains other classes defined here.
    It needs a position, and its width & height can
    be automatically set when adding new elements.

    The `select` method goes through a list of this
    object's selectable elements, and instead of 
    just using the object, the individual options
    are stored.

    Styles:
          GROUP      KEY
        - Label      value_style  : style of labels
        - Prompt     label_style  : prompt left
        - Prompt     value_style  : prompt right
        - Container  corner_style : style for corners
    """

    def __init__(self,pos=None,border=None,width=None,height=None,dynamic_size=True,center_elements=True,padding=0):
        # sanitize width
        if not width == None:
            self.width = min(width,WIDTH)
        else:
            self.width = 0

        # sanitize height
        if not height == None:
            self.height = min(height,HEIGHT-2)
        else:
            self.height = 0
        self.real_height = self.height

        # set default position
        if pos == None:
            pos = [0,0]
        self.pos = pos

        # set up values
        self.previous_pos = None
        self.previous_repr = None
        self.padding = padding

        self.elements = []
        self.selected = None
        self.selectables = []
        self.selected_index = 0

        self.styles = {}
        self.centering_axis = "both"
        self.corners = [[],[],[],[]]
        self.corner_style = CONTAINER_CORNER_STYLE

        # set up border
        if border == None:
            border = CONTAINER_BORDER_CHARS
        self.border_style = CONTAINER_BORDER_STYLE
        self.set_borders(border())

        # set up flags
        self._do_dynamic_size = dynamic_size
        self._do_center_elements = center_elements
        self._is_centered = False

        # optional flag to avoid wiping
        self._has_printed = True
        

    # set style for element type `group`
    def set_style(self,group,key,value):
        # non group items
        if group == type(self):
            setattr(self,key+'_style',value)
            return

        if not group in self.styles.keys():
            self.styles[group] = {}

        self.styles[group][key] = value

        for e in self.elements:
            if type(e) == group:
                e.set_style(key,value)


    # text representation of self
    def __repr__(self):
        global WIDTH,HEIGHT

        self._repr_pre()

        nWIDTH,nHEIGHT = os.get_terminal_size()
        if not [WIDTH,HEIGHT] == [nWIDTH,nHEIGHT]:
            # call event
            event__window_size_changed(self,[WIDTH,HEIGHT],[nWIDTH,nHEIGHT])

            WIDTH,HEIGHT = nWIDTH,nHEIGHT
            self._window_size_changed()


        line = ''
        new_real_height = 0

        # print elements
        x,starty = self.pos
        starty += 2
        x += 2

        # vertically center elements
        if self._do_center_elements:
            vertical_padding = max((self.real_height-sum(e.height for e in self.elements))//2,0)
            starty += vertical_padding

        # print all elements
        extra_lines = 0
        self.lines = []
        for i,e in enumerate(self.elements):
            if False and self._do_dynamic_size:
                self.width = min(max(self.width,e.width+4),WIDTH-4)
            e.width = self.width - 4

            # call event
            self._handle_long_element(e)

            e.pos = [x+1,starty+i]

            # get lines from element
            lines = repr(e).split('\n')

            # remove lines whos line_break returned empty
            if lines == [""] and not e.value == '':
                self.elements.remove(e)
                for o in self.selectables:
                    if o[0] == e:
                        self.selectables.remove(o)
                dbg('ERROR:',type(e),f'width ({e.width}) was too long or otherwise invalid, ignoring!')
                continue

            diff = len(lines)
            new_real_height += diff


            self.lines += lines
            for li,l in enumerate(lines):
                line += f"\033[{starty+i+li};{x}H"+(real_length(l)+2)*' '
                line += f"\033[{starty+i+li};{x}H "+l

            starty += diff-1

        
        if not self.real_height == new_real_height:
            self.real_height = new_real_height
            self.height = new_real_height
        self.get_border()

        # print border
        py = None
        for x,y,char in self.border[:]:
            # set previous y
            py = y

            # write to stdout
            line += f'\033[{y};{x}H'+char

        self.previous_repr = line
        return line


    # internal function to add elements
    def _add_element(self,element):
        # set width for element if none is available
        if element.width == None:
            element.width = self.width

        # update self sizing
        if self.width == None or self._do_dynamic_size:
            # if element is too wide selt self width to it+pad
            if WIDTH-5 > element.width >= self.width:
                self.width = element.width+3

            # if element is too tall set self height
            if self.real_height+element.height >= self.height:
                self.height = self.real_height+element.height

        # run element to update its values
        repr(element)

        # add padding
        for _ in range(self.padding):
            e = Label("")
            self.elements.append(e)
            self.real_height += e.height
            self.height += e.height

        self.elements.append(element)
        element.parent = self

        # update real_height
        self.real_height += element.height
        self.height += element.height

        # add selectables
        if element._is_selectable:
            # set options for range
            if element.options == None:
                options = 1
            else:
                options = len(element.options)

            # go through options, add element+index_in_element,index_in_container
            for i in range(options):
                self.selectables.append([element,i,len(self.selectables)+i])

        # update border
        self.get_border()


    # set border values
    def set_borders(self,border):
        if len(border) == 1:
            border = border[0]
            self.borders = [border,border,border,border]
        elif len(border) == 2:
            sides,topbottom = border
            self.borders = [sides,topbottom,sides,topbottom]
        elif len(border) == 3:
            left,top,right = border
            self.borders = [left,top,right,top]
        elif len(border) == 4:
            self.borders = border

    
    # set border corners
    def set_corner(self,corner,value,offset=0):
        if not hasattr(self,'border'):
            self.get_border()

        # get values
        if corner in ["TOP_LEFT",0]:
            char = self.border[1]
            side = "left"
            index = 0

        elif corner in ["TOP_RIGHT",1]:
            char = self.border[1]
            side = "right"
            index = 1

        elif corner in ["BOTTOM_LEFT",2]:
            char = self.border[3]
            side = "left"
            index = 2

        elif corner in ["BOTTOM_RIGHT",3]:
            char = self.border[3]
            side = "right"
            index = 3

        else:
            raise Exception('Corner position '+str(corner)+' could not be handled.')

        # get & replace indexes
        px,py = self.pos

        ## get x
        if side == 'right':
            startx = px+self.width+2 - real_length(value) - offset
        elif side == 'left':
            startx = px+1 + offset

        ## get y
        if char == self.border[1]:
            y = py+1
        elif char == self.border[3]:
            y = py+self.real_height+2+self.padding

        # insert new
        new = []
        for x,char in zip(range(startx,startx+real_length(value)),value):
            new.append([x,y,self.corner_style(char)])

        # filter duplicates
        coords = [[x,y] for x,y,_ in self.border]
        newcoords = [[x,y] for x,y,_ in new]

        for i,c in enumerate(self.border):
            x,y,_ = c

            if [x,y] in newcoords:
                newindex = newcoords.index([x,y])
                self.border.pop(i)
                self.border.insert(i,new[newindex])

        self.corners[index] = [corner,value,offset]


    # get list of border coordinates
    def get_border(self):
        px,py = self.pos
        x1,y1 = px,py
        x1 += 1
        y1 += 1
        x2 = px+self.width+1
        y2 = py+self.real_height+2+self.padding

        left,top,right,bottom = [self.border_style(a) for a in self.borders]
        self.border = []
        for y in range(py+1,y2):
            if real_length(left):
                self.border.append([x1,y,left])
            if real_length(right):
                self.border.append([x2,y,right])

        for x in range(px+1,x2+1):
            if real_length(bottom):
                self.border.append([x,y2,bottom])
            if real_length(top):
                self.border.append([x,y1,top])

        for c in self.corners:
            if not len(c):
                continue
            corner,value,offset = c
            self.set_corner(corner,value,offset)


    # wrapper for _add_element to make bulk adding easier
    def add_elements(self,elements):
        if not isinstance(elements,list):
            elements = [elements]

        for e in elements:
            self._add_element(e)

        # check if everything is valid
        repr(self)


    # select index in selectables list
    def select(self,index=None):
        if index == None:
            index = self.selected_index

        # error if invalid index
        if len(self.selectables) == 0:
            return

        if index > len(self.selectables)-1:
            if VERBOSE:
                raise Exception("Index is not in elements.")
            else:
                index = len(self.selectables)-1

        # avoid < 0 indexes
        index = max(0,index)
        
        # set instance variables
        self.selected = self.selectables[index]
        self.selected_index = index

        # go through selectables
        target_element = self.selectables[index][0]
        for i,(e,sub_i,_) in enumerate(self.selectables):
            # check if current is the target
            if i == index:
                e.select(sub_i)
                
            # unselect element if 
            elif not target_element == self.selectables[i][0]:
                e._is_selected = False

        self._selection_changed(self,index)
  
    
    # go through object, wipe ever character contained
    def wipe(self,pos=None,force=False):
        if not self._has_printed or force:
            return

        if pos == None:
            pos = self.pos

        if self.pos == None:
            return

        px,py = pos
        for y in range(py+1,py+self.height+2):
            for x in range(px+1,px+self.width+2):
                sys.stdout.write(f'\033[{y};{x}H ')

        sys.stdout.flush()


    def wipe_all_containing(self):
        px,py = self.pos
        for y in range(py+1,py+self.height+3):
            sys.stdout.write(f'\033[{y};0H'+'\033[K')
        sys.stdout.flush()
    

    # transform self to new position
    def move(self,pos,wipe=False):
        self.pos = pos
        if wipe:
            self.wipe()
        self.get_border()


    # center container
    def center(self,axes=None,xoffset=0,yoffset=5):
        self.move([0,0])
        if not axes:
            axes = self.centering_axis

        self._is_centered = True
        if HEIGHT//2 < self.height-yoffset:
            yoffset = 0
        if WIDTH//2 < self.width-xoffset:
            xoffset = 0
        
        x,y = self.pos
        self.centering_axis = axes
        if axes == "both" or axes == "x":
            x = (WIDTH-self.width-xoffset)//2
        if axes == "both" or axes == "y":
            y = (HEIGHT-self.height-yoffset)//2
        self.move([x,y])


    def export(self,filename):
        if not filename.endswith('.ptg'):
            filename += '.ptg'

        with open(filename,'w') as f:
            f.write(repr(self))


    # EVENT: window size changed
    # - checked for during __repr__
    def _window_size_changed(self):
        clr()

        self.width = min(self.width,WIDTH-5)
        self.height = min(self.height,HEIGHT)

        if self._is_centered:
            self.center()

        self.get_border()


    # EVENT: check for long elements, handle them
    # - called during __repr__ element loop
    def _handle_long_element(self,e):
        if hasattr(e,'label') and hasattr(e,'value') and not isinstance(e.value,dict):
            # check value length
            if real_length(str(e.value))+4 > self.width*(1/3):
                # check if self can be extended
                if e.width+10 < WIDTH*(1/2) and e.width < self.width:
                    self.width = e.width+10
                    e.real_value = e.value
                else:
                    e.real_value = e.value
                    e.value = '...'
                
            # second check
            if real_length(str(e.label))+4 > self.width*(1/2):
                e.label = str(e.label)[:int(self.width*(1/3))-3]+'...'


    # EVENT: start of repr
    # - called before any repr logic
    def _repr_pre(self):
        return

    # EVENT: selection changed
    # - called during select() method, useful in extending select behaviour
    @staticmethod
    def _selection_changed(self,index):
        return

class Prompt:
    """ 
    A class to display an optional label, along with choices.
    There are two layouts: "<label> [option]" and a centered
    list of options. 

    If there is a label given during construction the first 
    option is chosen, and the options given are disregarded.

    Styles:
        - short_highlight_style : used for type 1
        - long_highlight_style  : used for type 2
        - label_style           : used for labels in type1 of prompt
        - value_style           : used for values (between [ and ],
                                  non-inclusive.)
    """
    
    def __init__(self,width=None,options=None,label=None,real_label=None,justify_options='center',value="",padding=0): 
        # the existence of label decides the layout (<> []/[] [] [])
        if label:
            self.label = str(label)
            if real_label == None:
                self.real_label = clean_ansi(self.label)
            else:
                self.real_label = real_label

            self.width = real_length(self.real_label)+real_length(value)
        else:
            self.label = label
            self.width = width
            self.real_label = label

        # set up dimensions
        self.height = 1

        # set up instance variables
        self.selected_index = None
        self.options = options
        self.padding = padding
        self.value = value
        self.real_value = self.value

        # styles
        self.long_highlight_style = PROMPT_LONG_HIGHLIGHT_STYLE
        self.short_highlight_style = PROMPT_SHORT_HIGHLIGHT_STYLE
        self.label_style = PROMPT_LABEL_STYLE
        self.value_style = PROMPT_VALUE_STYLE
        self.delimiter_style = PROMPT_DELIMITER_STYLE
        self.justify = justify_options
        
        # flags
        self._is_selectable = True
        self._is_selected = False


    # return string representation of self
    def __repr__(self):
        if hasattr(self,'custom_repr'):
            return self.custom_repr(self)

        delimiters = []
        style = self.delimiter_style()

        if not style == None:
            for i,v in enumerate(self.delimiter_style()):
                if i % 2 == 0:
                    delimiters.append(v+' ')
                else:
                    delimiters.append(' '+v)

            start,end = delimiters[:2]
        else:
            # start,end = '   ','   '
            start,end = '',''

        
        # if there is a label do <label> [ ]
        if not self.label == None:
            label = self.label_style(self.label)
            value = self.value_style(self.value)

            highlight_len = real_length(self.long_highlight_style(''))
            highlight = (self.long_highlight_style if self._is_selected else lambda item: highlight_len*' '+item)
            middle_pad = (self.width-real_length(label)) - real_length(start+end) - real_length(value) - max(self.padding,2)
            middle_pad = max(2,middle_pad)

            left = ' ' + label + middle_pad*" "
            right = start + value + end

            line = (self.padding-1-highlight_len)*' '+highlight(left + right)+'  '
            self.width = max(self.width,real_length(line))

        # else print all options
        else:
            # set up line
            line = ''
            if isinstance(self.options, list):
                for i,option in enumerate(self.options):
                    option = self.value_style(str(option))
                    line += self._get_option_highlight(i,'short')(start+option+end)+'  '
            else:
                line = self.value_style(self.value)

            # center all lines 
            lines = break_line(line,_len=self.width-3,_separator="  ")

            if lines == []:
                if VERBOSE:
                    raise Exception("Lines are empty, likely because the given length was too short.")
                else:
                    return ""
            
            if self.justify == 'center':
                for i,l in enumerate(lines):
                    l_len = real_length(l)
                    pad = ( (self.width-l_len)//2 + self.padding + 2) * " "
                    lines[i] = pad + l + pad

            elif self.justify == "left":
                for i,l in enumerate(lines):
                    lines[i] = self.padding*' '+l

            elif self.justify == "right":
                for i,l in enumerate(lines):
                    pad = self.width-real_length(lines[i])-self.padding+2
                    lines[i] = pad*' '+l
                
            # set new hight, return line
            self.height = len(lines)
            line = "\n".join(lines) 
        
        return line


    # get highlight value for index in options
    def _get_option_highlight(self,index,which='long'):
        if self._is_selected and self.selected_index == index:
            return getattr(self,which+'_highlight_style')
        else:
            return lambda item: item


    # select index in options
    def select(self,index=0):
        self._is_selected = True
        self.selected_index = index

        if isinstance(self.options,list):
            self.value = self.options[index]
            self.real_value = self.value
        return self.value


    # set style
    def set_style(self,key,value):
        setattr(self,key+'_style',value)


    # method to overwrite
    def submit(self):
        if hasattr(self,'real_value'):
            return self.real_value
        else:
            return self.value

class Label:
    """ 
    A simple, non-selectable object for printing text

    Styles:
        - value_style : style for string value of label
    """
    def __init__(self,value="",justify="center",width=None,padding=1):
        # values
        self.value = value
        self.height = 1

        # set width
        if not width == None:
            self.width = width
        else:
            self.width = real_length(self.value)+3

        self.justify = justify
        self.padding = padding
        self.value_style = LABEL_VALUE_STYLE


        # flags
        self._is_selectable = False
        self._is_selected = False

    def set_value(self,value):
        self.value = value
        self.width = real_length(self.value)+3
        
    def __repr__(self):
        lines = break_line(self.value_style(self.value),_len=self.width-self.padding)

        if self.justify == "left":
            # nothing needs to be done
            for i,l in enumerate(lines):
                lines[i] = self.padding*' '+l

        elif self.justify == "center":
            for i,l in enumerate(lines):
                pad = ((self.width-real_length(l))//2+1)*' '
                lines[i] = pad + l + pad

        elif self.justify == "right":
            for i,l in enumerate(lines):
                pad = (self.width-real_length(l))*' '
                lines[i] = pad + l

        self.height = len(lines)
        return "\n".join(lines)
        
    # set style of key to value
    def set_style(self,key,value):
        setattr(self,key+'_style',value)



# GLOBALS #

# global width & height -- refreshed at every new object creation
WIDTH,HEIGHT = os.get_terminal_size()

# element_id - object
ELEMENT_IDS = {}

# element_id - [attribute,value]
## this is applied in set_element_id, to every element
## matching the given element_id
ELEMENT_ATTRIBUTES = {}

# styles
## other
DEFAULT_COLOR_PREFIX = "38;5"
GLOBAL_HIGHLIGHT_STYLE = Color.highlight
CURSOR_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE
TABBAR_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE

# container
CONTAINER_BORDER_CHARS  = lambda: "|-"
CONTAINER_BORDER_STYLE  = lambda item: item
CONTAINER_CORNER_STYLE  = lambda item: item
CONTAINER_LABEL_STYLE   = lambda item: item
CONTAINER_VALUE_STYLE   = lambda item: item
CONTAINER_CORNER_STYLE  = lambda char: char
CONTAINER_TITLE_STYLE   = lambda item: Color.italic(Color.bold(item))
CONTAINER_ERROR_STYLE   = lambda item: Color.color(Color.bold(item),'38;5;196')
CONTAINER_SUCCESS_STYLE = lambda item: Color.color(Color.bold(item),'2')

## prompt
PROMPT_LABEL_STYLE = lambda item: item
PROMPT_VALUE_STYLE = lambda item: item
PROMPT_DELIMITER_STYLE = lambda: '[]'
PROMPT_SHORT_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE
PROMPT_LONG_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE

## label
LABEL_VALUE_STYLE = lambda item: item


# client global
VERBOSE = 0


def perspective(color,index):
    chars = ( (WIDTH-1) ) * '█'
    gradient1 = get_gradient(color)
    gradient2 = list(reversed(gradient1))[1:]
    values = gradient1+gradient2

    adjusted = index+1
    values.insert(adjusted,values[adjusted])


    line = gradient(chars,values)
    for _ in range(HEIGHT):
        print(line)


# TEST CODE #
if __name__ == "__main__":
    pass
