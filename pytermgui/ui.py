"""
pytermgui.ui
------------
author: bczsalba


File providing UI classes to display data and user interactions.

All classes defined here are subclassed from BaseElement, and in the future
custom object creation will be supported in this manner.
"""

import re
import os
import sys
import time
from typing import Callable, Any, Iterable, Union, IO, Optional
from .helpers import clean_ansi, real_length, break_line
from . import (
    color,
    bold,
    italic,
    gradient,
    highlight,
    underline,
    get_gradient,
    strikethrough,
)
from .globals import *


try:
    import pyperclip as clip

    USE_CLIPBOARD = True
except ImportError:
    USE_CLIPBOARD = False


# HELPERS #
def dbg(*args, **kwargs):
    print(*args, **kwargs)


def set_debugger(fun):
    globals()["dbg"] = fun


def wipe():
    print("\033[2J\033[H")


def _assert_style(value):
    assert isinstance(value, Callable), f'\nStyle value "{value}" is not callable.'
    try:
        tester = value(0, "test")
    except ValueError as e:
        dbg(f"Could not check return type of {value}: {e}")
        return

    except TypeError as e:
        raise AssertionError(
            f"Style value {value} could not take the arguments: [depth: int, item: str]:\nError: {e}"
        )

    assert isinstance(
        tester, str
    ), f"\nReturn of {value} is type {type(tester)}, not str."


def _get_obj_from_str(name: str):
    obj_type = globals()[name]
    assert issubclass(obj_type, BaseElement)

    return obj_type()


def _get_style_source(fun: Callable):
    assert callable(fun)
    import inspect

    return inspect.getsource(fun)


# DATA SETTERS
def set_style(key: str, value: Callable[[int, str], str]):
    if not key.endswith("_chars"):
        _assert_style(value)
    key = key.upper()

    if key in globals():
        globals()[key] = value
    else:
        globals()[key + "_STYLE"] = value

    return key + "_STYLE"


def set_element_id(element: object, element_id: Any):
    element.id = element_id
    ELEMENT_IDS[element_id] = element

    # set given attributes
    if not ELEMENT_ATTRIBUTES.get(element_id) == None:
        for attribute, value in ELEMENT_ATTRIBUTES[element_id].items():
            setattr(element, attribute, value)


# set attributes to be applied to all elements matching id
def set_attribute_for_id(element_id: Any, key: str, value: str):
    if element_id in ELEMENT_ATTRIBUTES.keys():
        ELEMENT_ATTRIBUTES[element_id][key] = value
    else:
        ELEMENT_ATTRIBUTES[element_id] = {key: value}

    obj = get_object_by_id(element_id)
    if obj:
        setattr(obj, key, value)


def set_listener(event: str, func: Callable):
    globals()["event__" + event] = func


# DATA GETTERS
def get_object_by_id(key: str):
    return ELEMENT_IDS.get(key)


def get_style(name: str):
    name = name.upper() + "_STYLE"
    if name in globals():
        return globals()[name]
    else:
        return lambda *args: None


# EXCEPTIONS #
class SerializeError(Exception):
    """ Exception raised by miscellaneous serialization operations """

    pass


class LoadError(SerializeError):
    """ Exception raised during _load methods """

    pass


class DumpError(SerializeError):
    """ Exception raised during _dump methods """

    pass


# CLASSES #
class BaseElement:
    """ Element that all classes here derive from """

    def __init__(self):
        self.id = None
        self.width = 0
        self.height = 1
        self.static_width = None
        self.real_height = self.height
        self.pos = [0, 0]
        self.parent = None
        self.depth = 0

        self.is_selectable = True
        self._is_selected = False

        self._serializable = []

    def __add__(self, other):
        """
        Allows for the syntax:
            c = Label('title') + Prompt('input')
        """
        if isinstance(other, Container) and not isinstance(self, Container):
            other.add_elements(self)
            return other

        if self.parent:
            c = self.parent
        else:
            c = Container()
            c.add_elements(self)

        c.add_elements(other)

        return c

    def _dump(self, bake=False):
        d = {}
        for value in self._serializable:
            # check for (value, style) tuples
            if isinstance(value, tuple):
                if not len(value) == 2:
                    raise DumpError("Tuples in _serialiable have to be of length two")

                # get values from tuple
                _val, _style = value
                val = getattr(self, _val)
                style = getattr(self, _style)

                # add raw value if not baking
                if not bake:
                    d[_val] = val
                    continue

                if not callable(style):
                    raise DumpError(f"Value for style ({style}) is not callable.")

                # add styled val
                d[_val] = style(self.depth, val)
                continue

            else:
                if value.endswith("()"):
                    value = value.strip("()")
                    if callable(value):
                        d[value] = getattr(self, value)()
                        continue

                # add raw data
                d[value] = getattr(self, value)

        return d

    def _get_serializable(self):
        serializable = []
        for value in self._serializable:
            if isinstance(value, tuple):
                serializable.append(value[0])
            else:
                serializable.append(value.strip("()"))
        return serializable

    def _load(self, data):
        for key, value in data.items():
            if not key in self._get_serializable() and not key == "type":
                raise LoadError(
                    f'Field "{key}" is not serializable for type {self.name()}.'
                )

            else:
                setattr(self, key, value)

        return self

    def wipe(self):
        line = ""
        x, y = self.pos
        if isinstance(self, Prompt) and self.justify == "right":
            x += 2

        container_offset = 1 if isinstance(self, Container) else 0
        for i in range(container_offset, self.height + container_offset):
            line += (
                f"\033[{y+i};{x+container_offset}H"
                + (self.width + container_offset) * " "
            )

        print(line, end="", flush=1)

    def name(self):
        return type(self).__name__

    def set_style(self, key: str, value: Callable[[int, str], str]):
        if not key.endswith("_chars"):
            _assert_style(value)

            if not key.endswith("_style"):
                key += "_style"

        setattr(self, key, value)


class Container(BaseElement):
    """
    An object which contains all elements under BaseElement, even its own type.

    Style groups:
        - Label
        - Prompt
        - Container
    Check individual classes for more details.

    Styles for Container & its children:
        all styles are called with arguments (depth,style)
        (ones marked with * are only checked on __init__, otherwise need to be set with their respective setters)
        - *border_chars              = characters to use for border, [left,top,right,bottom]
        - border_style               = style for border characters
        - *corner_chars              = characters to use for corners, [l_top,r_top,r_bottom,l_bottom]
        - corner_style               = style for corner characters
        - label_style                = style for Prompt.label
        - value_style                = style for Prompt.value
        - title_style                = style for ui__title elements from container_from_dict
        - error_style                = style for ui__error_title elements from container_from_dict
        - success_style              = style for ui__success_title elements from container_from_dict
    """

    def __init__(
        self,
        pos: list[int, int] = None,
        border: Iterable[str] = None,
        width: int = 40,
        height: int = None,
        dynamic_size: bool = True,
        center_elements: bool = True,
        shorten_elements: bool = True,
        padding: int = 0,
    ):

        super().__init__()

        # sanitize width
        if not width == None:
            self.width = min(width, WIDTH)
        else:
            self.width = 0

        # sanitize height
        if not height == None:
            self.height = min(height, HEIGHT - 2)
        else:
            self.height = 2
        self.real_height = self.height

        # set default position
        if pos == None:
            pos = [0, 0]
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
        self.depth = 0

        # set up border
        self.corners = [[], [], [], []]
        if border == None:
            border = CONTAINER_BORDER_CHARS
        self.border_style = CONTAINER_BORDER_STYLE
        self.set_borders(border())

        self.corner_style = CONTAINER_CORNER_STYLE
        corners = CONTAINER_CORNER_CHARS
        for i, c in enumerate(corners()):
            self.set_corner(i, c)

        self.shorten_elements = shorten_elements

        # set up flags
        # this is broken in many ways, and need for it is not certain.
        self._do_center_elements = True  # center_elements
        self._is_centered = False
        self._is_selected = True

        # optional flag to avoid wiping
        self._has_printed = True

        # list of serializable attributes
        self._serializable = [
            "id",
            "width",
            "height",
            "static_width",
            "shorten_elements",
            "pos",
            "padding",
            "borders",
            "corners",
        ]

    # text representation of self
    def __repr__(self):
        global WIDTH, HEIGHT

        self._repr_pre()
        if not self._is_selected:
            if self.selected:
                self.selected[0]._is_selected = False
        else:
            if self.selected:
                self.selected[0]._is_selected = True

        nWIDTH, nHEIGHT = os.get_terminal_size()
        if not [WIDTH, HEIGHT] == [nWIDTH, nHEIGHT]:
            # call event
            event__window_size_changed(self, [WIDTH, HEIGHT], [nWIDTH, nHEIGHT])

            WIDTH, HEIGHT = nWIDTH, nHEIGHT
            self._window_size_changed()

        line = ""
        new_real_height = 2

        self.width = min(WIDTH - 1, self.width)
        x, starty = self.pos
        starty += 1
        x += 2

        # vertically center elements
        if self._do_center_elements:
            vertical_padding = max(
                (self.real_height - sum(e.height for e in self.elements)) // 2, 0
            )
            starty += vertical_padding

        # print all elements
        extra_lines = 0
        self.lines = []
        for i, e in enumerate(self.elements):
            is_container = 1 if isinstance(e, Container) else 0

            if e.static_width is None:
                e.width = self.width - 3 - (1 if is_container else 0)

            # call event
            if self.shorten_elements:
                self._handle_long_element(e)

            e.pos = [x + (self.width - e.width - 3) // 2, starty + i - is_container]
            line += repr(e)

            new_real_height += e.height
            starty += e.height - 1

        self.real_height = new_real_height
        self.height = new_real_height
        self.get_border()

        # print border
        for x, y, char in self.border[:]:
            # write to stdout
            line += f"\033[{y};{x}H" + char

        self.previous_repr = line
        return line

    # overwrite add to not create new objects
    def __add__(self, other):
        assert self is not other

        if isinstance(other, Container):
            if id(self.elements) == id(other.elements):
                raise TypeError(
                    "The id-s of the list of elements for (self,other) cannot be identical."
                )

            assert (
                self not in other.elements
            ), f"You cannot add an element that this object is already a part of."

        elif isinstance(other, list):
            c = Container()
            c.add_elements(other)
            other = c

        self._add_element(other)
        return self

    # overwrite iadd to not create new objects
    def __iadd__(self, other):
        self = self + other
        repr(self)
        return self

    # index into elements
    def __getitem__(self, item):
        return self.elements[item]

    # get len of elements
    def __len__(self):
        return len(self.elements)

    # iterate through elements
    def __iter__(self):
        for e in self.elements:
            yield e

    # internal function to add elements
    def _add_element(self, element: BaseElement):
        assert issubclass(
            type(element), BaseElement
        ), f"Object of type {type(element)} is not a subclass of BaseElement."

        def _update_children_depth(element):
            current = element.depth + 1
            if isinstance(element, Container):
                for e in element:
                    e.depth = current
                    _update_children_depth(e)

        def _get_deep_selectables(element):
            if isinstance(element, Container):
                options = []
                for e in element:
                    new = _get_deep_selectables(e)
                    options += new
                return options

            elif element.is_selectable:
                if element.options:
                    return element.options
                else:
                    return [element]
            else:
                return []

        container_offset = 3 if isinstance(element, Container) else 0
        if element.static_width is not None:
            element.width = element.static_width

        elif (
            element.width is not None
            and not self.static_width
            and element.width >= self.width
        ):
            self.width = element.width + 1

        else:
            element.width = self.width - container_offset

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
        if element.is_selectable:
            # set options for range
            if isinstance(element, Container):
                options = len(_get_deep_selectables(element))
            elif element.options == None:
                options = 1
            else:
                options = len(element.options)

            # go through options, add element+index_in_element,index_in_container
            for i in range(options):
                self.selectables.append([element, i, len(self.selectables) + i])

        element.depth = self.depth + 1
        _update_children_depth(element)

        # update border
        self.get_border()

    # save json representation of self
    def _dump(self, bake=False):
        # set up base dictionary
        d = {
            "type": self.name(),
        }

        # run base _dump method
        for key, value in BaseElement._dump(self, bake).items():
            d[key] = value

        # set custom border
        d["borders"] = [self.border_style(self.depth, b) for b in self.borders]

        # do routine to add elements
        d["elements"] = []
        for e in self.elements:
            data = {}
            if not "type" in data.keys():
                data["type"] = e.name()

            for key, value in e._dump(bake).items():
                data[key] = value

            d["elements"].append(data)

        return d

    # load data from json
    def _load(self, data: dict):
        for key, value in data.items():
            if key == "elements":
                for e in value:
                    _type = e.get("type")
                    assert _type, e

                    obj = _get_obj_from_str(_type)
                    self._add_element(obj._load(e))

            elif not key in self._get_serializable() and not key == "type":
                raise LoadError(
                    f'Field "{key}" is not serializable for type {self.name()}.'
                )

            else:
                setattr(self, key, value)

        return self

    # pop method
    def pop(self, index=-1):
        removed = self.elements.pop(index)
        repr(self)
        return removed

    # insert element to index, naive
    def insert(self, index: int, element: BaseElement):
        elements = self.elements.copy()
        self._add_element(element)
        added = self.elements.pop(-1)

        elements.insert(index, added)
        self.elements = elements

    # remove method
    def remove(self, element):
        ret = self.elements.remove(element)
        repr(self)
        return ret

    # set style for element type `group`
    def set_style(self, group: BaseElement, key: str, value: Callable[[int, str], str]):
        if not key.endswith("_chars"):
            _assert_style(value)

        # non group items
        if group == type(self):
            setattr(self, key + "_style", value)
            return

        if not group in self.styles.keys():
            self.styles[group] = {}

        self.styles[group][key] = value

        for e in self.elements:
            if type(e) == group:
                e.set_style(key, value)

    # set border values
    def set_borders(self, border: Iterable[str]):
        if border == None:
            self.borders = ["", "", "", ""]

        elif len(border) == 1:
            border = border[0]
            self.borders = [border, border, border, border]
        elif len(border) == 2:
            sides, topbottom = border
            self.borders = [sides, topbottom, sides, topbottom]
        elif len(border) == 3:
            left, top, right = border
            self.borders = [left, top, right, top]
        elif len(border) == 4:
            self.borders = border

    # set border corners
    def set_corner(self, corner: Union[str, int], value: str, offset: int = 0):
        if not hasattr(self, "border"):
            self.get_border()

        if not len(self.border):
            return

        # get values
        if corner in ["TOP_LEFT", 0]:
            char = self.border[1]
            side = "left"
            index = 0

        elif corner in ["TOP_RIGHT", 1]:
            char = self.border[1]
            side = "right"
            index = 1

        elif corner in ["BOTTOM_LEFT", 2]:
            char = self.border[3]
            side = "left"
            index = 2

        elif corner in ["BOTTOM_RIGHT", 3]:
            char = self.border[3]
            side = "right"
            index = 3

        else:
            raise Exception("Corner position " + str(corner) + " could not be handled.")

        # get & replace indexes
        px, py = self.pos

        ## get x
        if side == "right":
            startx = px + self.width + 2 - real_length(value) - offset
        elif side == "left":
            startx = px + 1 + offset

        ## get y
        if char == self.border[1]:
            y = py + 1
        elif char == self.border[3]:
            y = py + self.real_height + self.padding

        # insert new
        new = []
        for x, char in zip(range(startx, startx + real_length(value)), value):
            new.append([x, y, self.corner_style(self.depth, char)])

        # filter duplicates
        coords = [[x, y] for x, y, _ in self.border]
        newcoords = [[x, y] for x, y, _ in new]

        for i, c in enumerate(self.border):
            x, y, _ = c

            if [x, y] in newcoords:
                newindex = newcoords.index([x, y])
                self.border.pop(i)
                self.border.insert(i, new[newindex])

        self.corners[index] = [corner, value, offset]

    # get element in children matching key
    def get_object_by_id(self, key: str):
        for e in self.elements:
            if e.id == key:
                return e

        return None

    # get list of border coordinates
    def get_border(self):
        px, py = self.pos
        x1, y1 = px, py
        x1 += 1
        y1 += 1
        x2 = px + self.width + 1
        y2 = py + self.real_height + self.padding

        left, top, right, bottom = [
            self.border_style(self.depth, a) for a in self.borders
        ]
        self.border = []
        for y in range(y1, y2):
            if real_length(left):
                self.border.append([x1, y, left])
            if real_length(right):
                self.border.append([x2, y, right])

        for x in range(x1, x2 + 1):
            if real_length(bottom):
                self.border.append([x, y2, bottom])
            if real_length(top):
                self.border.append([x, y1, top])

        for c in self.corners:
            if not len(c):
                continue
            corner, value, offset = c
            self.set_corner(corner, value, offset)

    # wrapper for _add_element to make bulk adding easier
    def add_elements(self, elements: Union[BaseElement, list]):
        if not isinstance(elements, list):
            elements = [elements]

        for e in elements:
            self._add_element(e)

    # select index in selectables list
    def select(self, index: int = None):
        if index == None:
            index = self.selected_index

        # error if invalid index
        if len(self.selectables) == 0:
            return

        if index > len(self.selectables) - 1:
            index = len(self.selectables) - 1

        # avoid < 0 indexes
        index = max(0, index)

        # set instance variables
        self.selected = self.selectables[index]
        self.selected_index = index

        # go through selectables
        target_element = self.selectables[index][0]
        _could_select = False
        for i, (e, sub_i, _) in enumerate(self.selectables):
            # check if current is the target
            if i == index:
                e.select(sub_i)
                _could_select = True

            # unselect element if
            elif not target_element == self.selectables[i][0]:
                e._is_selected = False

        if _could_select:
            self._selection_changed(self, index)

    # go through object, wipe ever character contained
    def _wipe(self, pos: list[int, int] = None, force: bool = False):
        if not self._has_printed or force:
            return

        if pos == None:
            pos = self.pos

        if self.pos == None:
            return

        px, py = pos
        for y in range(py, py + self.real_height + 1):
            for x in range(px + 1, px + self.width + 2):
                sys.stdout.write(f"\033[{y};{x}H ")

        sys.stdout.flush()

    def wipe_all_containing(self):
        px, py = self.pos
        for y in range(py + 1, py + self.height + 3):
            sys.stdout.write(f"\033[{y};0H" + "\033[K")
        sys.stdout.flush()

    # transform self to new position
    def move(self, pos: list[int, int], do_wipe: bool = False):
        self.pos = pos
        if do_wipe:
            self.wipe()
        self.get_border()

        return self

    # center container
    def center(self, axes: str = None, xoffset: int = 0, yoffset: int = 5):
        self.move([0, 0])

        repr(self)
        if not axes:
            axes = self.centering_axis

        self._is_centered = True
        if HEIGHT // 2 < self.height - yoffset:
            yoffset = 0
        if WIDTH // 2 < self.width - xoffset:
            xoffset = 0

        x, y = self.pos
        self.centering_axis = axes
        if axes == "both" or axes == "x":
            x = (WIDTH - self.width - xoffset) // 2
        if axes == "both" or axes == "y":
            y = (HEIGHT - self.height - yoffset) // 2
        self.move([x, y])

        return self

    # save raw characters as a file
    def export(self, filename: str):
        if not filename.endswith(".ptg"):
            filename += ".ptg"

        with open(filename, "w") as f:
            f.write(repr(self))

    def submit(self):
        selected = self.selected[0]
        try:
            return selected.submit()
        except TypeError:
            return selected.submit(selected)

    def _handle_long_element(self, e: BaseElement):
        if (
            hasattr(e, "label")
            and hasattr(e, "value")
            and not isinstance(e.value, dict)
        ):
            # check value length
            if real_length(str(e.value)) + 4 > self.width * (1 / 3):
                # check if self can be extended
                if (
                    e.width + 10 < WIDTH * (1 / 2)
                    and e.width < self.width
                    and not self.static_width
                ):
                    self.width = e.width + 10
                    e.real_value = e.value
                else:
                    e.real_value = e.value
                    e.value = "..."

            # second check
            if real_length(str(e.label)) + 4 > self.width * (1 / 2):
                e.label = str(e.label)[: int(self.width * (1 / 3)) - 3] + "..."

    # EVENT: window size changed
    # - checked for during __repr__
    def _window_size_changed(self):
        wipe()

        self.width = min(self.width, WIDTH - 5)
        self.height = min(self.height, HEIGHT)

        if self._is_centered:
            self.center()

        self.get_border()

    # EVENT: start of repr
    # - called before any repr logic
    def _repr_pre(self):
        return

    # EVENT: selection changed
    # - called during select() method, useful in extending select behaviour
    @staticmethod
    def _selection_changed(self, index: int):
        return


class Prompt(BaseElement):
    """
    A selectable & interactable object.

    Can have two different layouts:
                 ----------------------------
        - short: | < option1 >  < option2 > |
                 ----------------------------
        - long : | value1:      < option1 > |
                 ----------------------------

    The layout gets chosen according to whether the prompt has a
    label set. If yes, the long format is chosen, otherwise the
    short one is used.


    Styles:
        - short_highlight_style(item) : used for highlight of short type
        - long_highlight_style(item)  : used for highlight of long type

        - delimiter_chars()           : used for to set characters between
                                        which options are printed

        - label_style(item)           : used for labels
        - value_style(item)           : used for values (between delimiters,
                                        non-inclusive.)
    """

    def __init__(
        self,
        label: str = None,
        value: str = "",
        width: int = None,
        options: list[str] = None,
        real_label: str = None,
        justify_options: str = "center",
        padding: int = None,
    ):
        super().__init__()

        # the existence of label decides the layout (<> []/[] [] [])
        if label:
            self.label = str(label)
            if real_label == None:
                self.real_label = clean_ansi(self.label)
            else:
                self.real_label = real_label

            self.width = real_length(self.real_label) + real_length(value)
        else:
            self.label = label
            self.width = width
            self.real_label = label

        # set up dimensions
        self.height = 1

        # set up instance variables
        self.selected_index = 0
        self.options = options
        self.padding = padding
        self.value = value
        self.real_value = value

        # styles
        self.long_highlight_style = PROMPT_LONG_HIGHLIGHT_STYLE
        self.short_highlight_style = PROMPT_SHORT_HIGHLIGHT_STYLE
        self.label_style = PROMPT_LABEL_STYLE
        self.value_style = PROMPT_VALUE_STYLE
        self.delimiter_chars = PROMPT_DELIMITER_CHARS
        self.justify = justify_options

        if self.options:
            if callable(self.delimiter_chars):
                delims = self.delimiter_chars()
            else:
                delims = self.delimiter_chars

            if not delims:
                delim_length = 0
            else:
                delim_length = len(delims)
            self.width = sum(len(str(o)) for o in self.options) + delim_length + 3

        else:
            _label = ""
            _value = ""
            if label:
                _label = self.label
            if value:
                _value = self.value

            self.width = len(_label + _value)
            if padding == None:
                padding = 2
                self.padding = 2

        if padding == None:
            self.padding = 0

        # flags
        self.is_selectable = True
        self._is_selected = False

        self._serializable = [
            "id",
            ("label", "label_style"),
            ("value", "value_style"),
            "delimiter_chars()",
            "is_selectable",
            "options",
            "padding",
            "justify",
            "pos",
        ]

    # return string representation of self
    def __repr__(self):
        delimiters = []

        if callable(self.delimiter_chars):
            style = self.delimiter_chars()
        else:
            style = self.delimiter_chars

        x, y = self.pos

        if style is None:
            start, end = "", ""

        else:
            for i, v in enumerate(style):
                if i % 2 == 0:
                    delimiters.append(v + " ")
                else:
                    delimiters.append(" " + v)

            start, end = delimiters[:2]

        # if there is a label do <label> [ ]
        if not self.label == None:
            label = self.label_style(self.depth, self.label)
            value = self.value_style(self.depth, self.value)

            highlight_len = real_length(self.long_highlight_style(0, ""))
            highlight = (
                self.long_highlight_style
                if self._is_selected
                else lambda depth, item: highlight_len * " " + item
            )
            middle_pad = (
                (self.width - real_length(label))
                - real_length(start + end)
                - real_length(value)
                - self.padding
            )
            middle_pad = max(2, middle_pad)

            left = label + middle_pad * " "
            right = start + value + end

            line = (
                f"\033[{y};{x}H"
                + (self.padding - highlight_len) * " "
                + highlight(self.depth, left + right)
            )

        # else print all options
        else:
            # set up line
            if isinstance(self.options, list):
                lines = []
                buff = ""
                for i, option in enumerate(self.options):
                    option = self.value_style(self.depth, str(option))
                    buff += (
                        self._get_option_highlight(i, "short")(
                            self.depth, start + option + end
                        )
                        + "  "
                    )

                    if real_length(buff) > self.width - 3 - len(style if style else ""):
                        lines.append(buff)
                        buff = ""
                        continue

                lines.append(buff)

            else:
                line = self.value_style(self.depth, self.value)
                lines = break_line(
                    line,
                    _len=self.width - 3 - len(self.delimiter_chars()),
                    _separator="  ",
                )

            if lines == []:
                if VERBOSE:
                    raise Exception(
                        "Lines are empty, likely because the given length was too short."
                    )
                else:
                    return ""

            if self.justify == "center":
                for i, l in enumerate(lines):
                    l_len = real_length(l)
                    pad = ((self.width - l_len) // 2 + self.padding + 2) * " "
                    lines[i] = pad + l + pad

            elif self.justify == "left":
                for i, l in enumerate(lines):
                    lines[i] = self.padding * " " + l

            elif self.justify == "right":
                for i, l in enumerate(lines):
                    pad = self.width - real_length(lines[i]) + 4 - self.padding
                    lines[i] = pad * " " + l

            # set new hight, return line
            self.height = len(lines)
            line = "\n".join(lines)
            line = ""
            for i, l in enumerate(lines):
                line += f"\033[{y+i};{x}H"
                line += l

        return line

    # get highlight value for index in options
    def _get_option_highlight(self, index: int, which: str = "long"):
        if self._is_selected and self.selected_index == index:
            return getattr(self, which + "_highlight_style")
        else:
            return lambda depth, item: item

    # select index in options
    def select(self, index: int = None):
        self._is_selected = True

        if index == None:
            index = self.selected_index

        if self.options and index > len(self.options) - 1:
            index = len(self.options) - 1

        self.selected_index = max(0, index)

        if isinstance(self.options, list):
            self.value = self.options[index]
            self.real_value = self.value
        return self.value

    # method to overwrite
    def submit(self):
        if hasattr(self, "real_value"):
            return self.real_value
        else:
            return self.value


class Label(BaseElement):
    """
    A simple, non-selectable object for printing text

    Styles:
        - value_style(item) : style for string value of label
    """

    def __init__(
        self,
        value: str = "",
        justify: str = "center",
        width: int = None,
        padding: int = 1,
    ):
        super().__init__()

        # values
        self.value = value
        self.height = 1

        # set width
        if not width == None:
            self.width = width
        else:
            self.width = real_length(self.value) + 3

        self.justify = justify
        self.padding = padding
        self.value_style = LABEL_VALUE_STYLE

        # flags
        self.is_selectable = False
        self._is_selected = False

        self._serializable = [
            "id",
            ("value", "value_style"),
            "justify",
            "padding",
            "pos",
        ]

    def set_value(self, value: str):
        self.value = value
        self.width = real_length(self.value) + 3

    def __repr__(self):
        lines = break_line(
            self.value_style(self.depth, self.value), _len=self.width - self.padding
        )

        if self.justify == "left":
            # nothing needs to be done
            for i, l in enumerate(lines):
                lines[i] = self.padding * " " + l

        elif self.justify == "center":
            for i, l in enumerate(lines):
                pad = ((self.width - real_length(l)) // 2 + 1) * " "
                lines[i] = pad + l + pad

        elif self.justify == "right":
            for i, l in enumerate(lines):
                pad = (self.width - real_length(l)) * " "
                lines[i] = pad + l

        self.height = len(lines)
        x, y = self.pos

        final = ""
        for i, l in enumerate(lines):
            final += f"\033[{y+i};{x}H" + l

        return final


class InputField(BaseElement):
    """
    Custom field object to display input.
    NOTE: this object only displays data it's sent, capturing needs to be
          done separately.

    Styles:
        - value_style     : style for field value
        - highlight_style : style for field.select()
    """

    def __init__(
        self,
        pos: list[int, int] = None,
        linecap: int = 0,
        default: str = "",
        prompt: str = "",
        xlimit: int = None,
        ylimit: int = None,
        print_at_start: bool = False,
        padding: int = 0,
    ):
        super().__init__()

        # set up instance variables
        self.value = default
        self.padding = padding
        self.cursor = len(self.value)
        self.selected = ""
        self.selected_start = 0
        self.selected_end = 0
        self.prompt = prompt
        self.empty_cursor_char = " "

        # TODO
        self.linecap = linecap
        self.xlimit = xlimit
        self.ylimit = ylimit

        # set position as needed
        if pos == None:
            _, tHeight = os.get_terminal_size()
            self.pos = [0, tHeight]
        else:
            self.pos = pos

        self.is_selectable = False
        self._strip_pasted_newlines = True

        self.value_style = INPUTFIELD_VALUE_STYLE
        self.highlight_style = INPUTFIELD_HIGHLIGHT_STYLE

        if print_at_start:
            # print
            self.print()

        self._serializable = [
            "id",
            ("value", "value_style"),
            "padding",
            "prompt",
            "xlimit",
            "ylimit",
            "pos",
        ]

    def send(self, key: str, _do_print: bool = False):
        # delete char before cursor
        if key == "BACKSPACE":
            if self.cursor > 0:  # real_length(self.prompt):
                left = self.value[: self.cursor - 1]
                right = self.value[self.cursor :]
                self.value = left + right
                self.cursor -= 1

        elif key == "CTRL_V" and USE_CLIPBOARD:
            left = self.value[: self.cursor]
            right = self.value[self.cursor :]
            paste = clip.paste()
            if self._strip_pasted_newlines:
                paste = paste.replace("\n", "")
            self.value = left + paste + right
            self.cursor += real_length(paste)

        # move left
        elif key == "ARROW_LEFT":
            self.cursor = max(self.cursor - 1, real_length(self.prompt))

        # move right
        elif key == "ARROW_RIGHT":
            self.cursor = min(self.cursor + 1, len(self.value))

        # TODO: history navigation, toggleable
        elif key in ["ARROW_DOWN", "ARROW_UP"]:
            key = ""

        # TODO
        # elif key == '\n':
        # pass

        else:
            if not (self.xlimit and len(self.value + key) > self.xlimit):
                # add character at cursor
                left = self.value[: self.cursor]
                right = self.value[self.cursor :]
                self.value = left + key + right
                self.cursor += len(key)

        if _do_print:
            self.print()

    # enable/disable (terminal) cursor
    def set_cursor_visible(self, value: bool):
        if value:
            print("\033[?25h")
        else:
            print("\033[?25l")

    # reset self.value
    def clear_value(self):
        self.wipe()
        self.value = ""
        self.cursor = len(self.value)
        self.print()

    # set value, cursor location, pass highlight
    def set_value(
        self,
        target: str,
        cursor: int = None,
        highlight: bool = True,
        force_cursor: bool = False,
        do_print: bool = True,
    ):
        # clear space
        self.wipe()

        # set new value
        self.value = target

        # set cursor auto
        if cursor == None or cursor > real_length(self.value) - 1 and not force_cursor:
            self.cursor = max(real_length(self.value) - 1, 0)

        # set cursor manual
        elif not cursor == None:
            self.cursor = cursor

        self.width = real_length(self.value)

        if do_print:
            # print self
            self.print(highlight=highlight)

    # clear the space occupied by input currently
    def wipe(self):
        x, y = self.pos
        lines = []
        buff = self.prompt
        for i, c in enumerate(self.value):
            if c == "\n":
                lines.append(buff)
                buff = ""
            else:
                buff += c
        lines.append(buff)

        for i, l in enumerate(lines):
            sys.stdout.write(
                f"\033[{y-i};{x}H" + (real_length(l) + self.padding + 2) * " "
            )

        # length = real_length(self.prompt+self.value)+2
        # sys.stdout.write(f'\033[{y};{x}H'+(length)*'a')
        sys.stdout.flush()

    # print self, flush and show highlight if set
    def print(
        self, return_line: bool = False, flush: bool = True, highlight: bool = True
    ):
        # set up two sides
        left = self.value[: self.cursor]
        right = self.value[self.cursor + 1 :]

        # get char under cursor to highlight
        if callable(self.empty_cursor_char):
            char = self.empty_cursor_char(self)
        else:
            char = self.empty_cursor_char

        if self.cursor > len(self.value) - 1:
            charUnderCursor = char
        else:
            charUnderCursor = self.value[self.cursor]

        # set highlighter according to highlight param
        if highlight:
            selected_text = self.highlight_style(self.depth, charUnderCursor)
        else:
            selected_text = charUnderCursor

        # construct line
        x, y = self.pos
        line = (
            f"\033[{y};{x}H"
            + self.padding * " "
            + self.value_style(self.depth, self.prompt + left)
            + selected_text
            + self.value_style(self.depth, right)
        )

        if return_line:
            return line

        # clear current
        self.wipe()
        # write to stdout
        sys.stdout.write(line)

        # flush if needed
        if flush:
            sys.stdout.flush()

    def visual(self, start: int = None, end: int = None):
        if start > end:
            temp = end
            end = start
            start = temp

        if start == None or start < real_length(self.prompt):
            start = self.cursor
        if end == None or end > len(self.value) - 1:
            end = real_length(self.value) - 1

        end += 1

        left = self.value[:start]
        selected = self.value[start:end]
        right = self.value[end:]

        self.selected = selected
        self.selected_start = start
        self.selected_end = end

        selected_text = self.highlight_style(self.depth, selected)

        self.wipe()
        line = (
            self.value_style(self.depth, self.prompt + left)
            + selected_text
            + self.value_style(self.depth, right)
        )

        # write to stdout
        x, y = self.pos
        sys.stdout.write(f"\033[{y};{x}H" + line)
        sys.stdout.flush()

    def submit(self):
        return self.value

    def __repr__(self):
        return self.print(return_line=1)


# EVENTS #
def event__window_size_changed(
    caller: object, new: list[int, int], old: list[int, int]
):
    pass


# UTILITY FUNCTIONS #
def container_from_dict(
    dic: dict, padding: int = 4, submit: Callable[[object], Any] = None, **kwargs
) -> list[Container]:
    """
    Create a container from elements of `dic`.

    If the current key isn't a special one, a Prompt object is created &
    added, with the value of the dict[key].

    special keys:
        General
        - ui__file:            str : sets element.file value
        - ui__reverse_keys    bool : temp = key; key = value; value = temp

        Labels
        - ui__label           dict : creates a Label with justify = dict.get('justify'),
                                     and value = dict.get('value')
        - ui__padding          any : creates Label() with no value
        - ui__title:           str : creates a Label, using `CONTAINER_TITLE_STYLE`
        - ui__success_title:   str : creates a Label, using `CONTAINER_SUCCESS_STYLE`
        - ui__error_title:     str : creates a Label, using `CONTAINER_ERROR_STYLE`

        Prompts
        - ui__button:         dict : creates Prompt with the singular option of
                                     dict.get('value'), and id = dict.get('id')
        - ui__prompt:         dict : creates Prompt with options = dict.get('options'),
        - ui__prompt_options: list : sets options for next non-special-key prompt

    parameters:
        - padding                  : sets amount of spaces after a *__title object
        - prompts_selectable       : sets Prompt.is_selectable value

    """

    dic_c = Container(**kwargs)

    dicts = [dic_c]
    reverse_items = False
    handler = None
    current_padding = 2
    prompt_options = None
    datafile = None
    element_id = None

    for i, (key, item) in enumerate(dic.items()):
        if key.startswith("ui__"):
            # GENERATOR OPTIONS
            ## set datafile for all objects
            if key == "ui__file":
                datafile = item

            ## read titles into labels
            elif "_title" in key:
                # get next title element
                for next_title, k in enumerate(list(dic.keys())[i + 1 :]):
                    if k.startswith("ui__title") and k[-1].isdigit():
                        break

                l = Label(value=item, justify="left")

                if key.startswith("ui__title"):
                    l.set_style("value", CONTAINER_TITLE_STYLE)

                elif key.startswith("ui__success_title"):
                    l.set_style("value", CONTAINER_SUCCESS_STYLE)

                elif key.startswith("ui__error_title"):
                    l.set_style("value", CONTAINER_ERROR_STYLE)

                # set id
                if not element_id == None:
                    set_element_id(l, element_id)
                    element_id = None

                height_with_segment = (
                    dicts[-1].real_height + next_title * (1 + dicts[-1].padding) + 5
                )

                if height_with_segment > HEIGHT - 5:
                    dicts.append(Container(**kwargs))
                    dicts[-1].add_elements(l)
                    continue

                # only pad if not the first element
                if not i == 0 and not list(dic.keys())[i - 1] == "ui__file":
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

                if submit:
                    p.submit = submit

                p.set_style("value", CONTAINER_VALUE_STYLE)

                if element_id:
                    set_element_id(p, element_id)
                    element_id = None

                dicts[-1].add_elements(p)

            ## create padder
            elif key.startswith("ui__padding"):
                p = Label()

                if element_id:
                    set_element_id(p, element_id)
                    element_id = None

                dicts[-1].add_elements(p)

            elif key.startswith("ui__button"):
                button = Prompt(options=[item.get("value")])
                button.set_style("value", CONTAINER_VALUE_STYLE)

                set_element_id(button, item.get("id"))

                dicts[-1].add_elements(button)

            elif key.startswith("ui__label"):
                justify = item.get("justify")
                value = item.get("value")
                padding = item.get("padding")

                if element_id:
                    set_element_id(p, element_id)
                    element_id = None

                label = Label(value=value, justify=justify, padding=padding)
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
            if isinstance(item, dict):
                length = len(item.keys())
                if length == 0:
                    continue
                else:
                    # item = "bl!"
                    item = "->"
                    delim = ""
            else:
                delim = None

            # create, add prompt
            p = Prompt(
                real_label=str(key),
                label=str(key),
                value=str(item),
                padding=current_padding,
            )
            p._internal_options = prompt_options
            if submit:
                p.submit = submit

            prompt_options = None
            p.set_style("label", CONTAINER_LABEL_STYLE)
            p.set_style("value", CONTAINER_VALUE_STYLE)
            p.real_value = real_value

            if element_id:
                set_element_id(p, element_id)
                element_id = None

            if not delim == None:
                p.delimiter_chars = lambda: ["   ", "{}"]
                p.set_style("value", CONTAINER_LABEL_STYLE)

            # add prompt to dict
            if dicts[-1].height + p.height > HEIGHT - 5:
                dicts.append(Container(**kwargs))

            dicts[-1].add_elements(p)

    do_tabline = len(dicts) > 1
    for i, d in enumerate(dicts):
        if not datafile == None:
            for e in d.elements:
                e.file = datafile
            d.file = datafile

        if do_tabline:
            tabline = Prompt(options=[n for n in range(len(dicts))])
            tabline.set_style("short_highlight", TABBAR_HIGHLIGHT_STYLE)
            tabline.select(i)
            tabline.is_selectable = False
            d.add_elements([Label(), tabline])

    return dicts


def loadd(data: dict) -> BaseElement:
    """ Load object from dictionary """

    import json

    _type = data.get("type")

    obj = _get_obj_from_str(_type)
    # del data['type']

    return obj._load(data)


def loads(data: str) -> BaseElement:
    """ Load object from str """

    import json

    return loadd(json.loads(data))


def load(fp: IO) -> BaseElement:
    """ Load object from file pointer """

    import json

    # print('val',fp.read())
    return loadd(json.load(fp))


def dumpd(obj: BaseElement, bake: bool = True) -> dict:
    """
    Dump BaseElement object to dict, baking in styles values if `bake`.
    This exists because obj._dump is a private method.

    Note: by baking, the styles becomes static.
    """

    return obj._dump()


def dumps(obj: BaseElement, bake: bool = True, **kwargs) -> str:
    """
    Dump BaseElement object to str, baking in styled values if `bake`.

    Note: by baking, the styles become static.
    """

    import json

    return json.dumps(obj._dump(bake), **kwargs)


def dump(obj: BaseElement, fp: IO, bake: bool = True, **kwargs) -> int:
    """
    Dump BaseElement object to fp (.write() supported object), baking in styled values if `bake`.

    Note: by baking, the styles become static.
    """

    import json

    return fp.write(dumps(obj, bake, **kwargs))


def load_from_file(name: str):
    """ Return BaseElement from filename """

    with open(name, "r") as f:
        obj = load(f)

    return obj


def dump_to_file(obj: BaseElement, name: str):
    """ Dump BaseElement to filename """

    with open(name, "w") as f:
        ret = dump(obj, f)

    return ret


def _export_styles() -> str:
    """ unfinished: export source for style settings """

    import inspect

    lines = []

    for style in SERIALIZED_STYLES:
        if isinstance(style, tuple):
            var, value = style
            lines.append(f"{var} = {value}")
            continue

        elif isinstance(style, str):
            value = globals()[style]
        else:
            value = style

        if callable(value):
            source = inspect.getsource(value)
            if source.count("\n") > 1:
                lines.append(" ".join(source.split(" ")).replace("@serialize", "", 1))
            else:
                if source.startswith("set_style"):
                    lines.append(" ".join(source.split()))

    lines.sort()
    lines.insert(0, STYLE_FILE_TEMPLATE)

    return "\n".join(lines)


def _serialize(data: Union[Callable[..., Optional[Any]], tuple[str, Any]]):
    """unused: add data to exported styles
    can be used as a wrapper or call"""

    # wrapper usage for functions
    if isinstance(data, Callable):
        SERIALIZED_STYLES.append(data)
        return data

    # call usage for variables
    elif isinstance(data, tuple):
        if not len(data) == 2:
            raise SerializeError("Expected tuple of length 2, got: " + str(data))
        SERIALIZED_STYLES.append(data)

    else:
        raise SerializeError(
            f"Expected Callable or tuple object, got {type(data)} with value {data}."
        )
