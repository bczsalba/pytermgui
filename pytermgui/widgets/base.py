"""
The basic building blocks making up the Widget system.
"""

# The classes defined here need more than 7 instance attributes,
# and there is no cyclic import during runtime.
# pylint: disable=too-many-instance-attributes, cyclic-import

from __future__ import annotations

from copy import deepcopy
from inspect import signature
from dataclasses import dataclass, field
from typing import Callable, Optional, Type, Iterator, Any

from ..input import keys
from ..parser import markup
from ..context_managers import cursor_at
from ..helpers import real_length, break_line
from ..exceptions import WidthExceededError, LineLengthError
from ..ansi_interface import terminal, clear, MouseEvent, MouseAction
from ..enums import SizePolicy, CenteringPolicy, HorizontalAlignment, VerticalAlignment

from . import boxes
from . import styles as w_styles


__all__ = ["MouseTarget", "MouseCallback", "Widget", "Container", "Label"]

MouseCallback = Callable[["MouseTarget", "Widget"], Any]
BoundCallback = Callable[..., Any]


def _set_obj_or_cls_style(
    obj_or_cls: Type[Widget] | Widget, key: str, value: w_styles.StyleType
) -> Type[Widget] | Widget:
    """Sets a style for an object or class

    Args:
        obj_or_cls: The Widget instance or type to update.
        key: The style key.
        value: The new style.

    Returns:
        Type[Widget] | Widget: The updated class.

    Raises:
        KeyError: The style key provided is invalid.
        ValueError: The style value is not callable.
    """

    if not key in obj_or_cls.styles.keys():
        raise KeyError(f"Style {key} is not valid for {obj_or_cls}!")

    if not callable(value):
        raise ValueError(f"Style {key} for {type(obj_or_cls)} has to be a callable.")

    obj_or_cls.styles[key] = value

    return obj_or_cls


def _set_obj_or_cls_char(
    obj_or_cls: Type[Widget] | Widget, key: str, value: w_styles.CharType
) -> Type[Widget] | Widget:
    """Sets a char for an object or class

    Args:
        obj_or_cls: The Widget instance or type to update.
        key: The char key.
        value: The new char.

    Returns:
        Type[Widget] | Widget: The updated class.

    Raises:
        KeyError: The char key provided is invalid.
    """

    if not key in obj_or_cls.chars.keys():
        raise KeyError(f"Char {key} is not valid for {obj_or_cls}!")

    obj_or_cls.chars[key] = value

    return obj_or_cls


@dataclass
class MouseTarget:
    """A target for mouse events."""

    parent: Widget
    """Parent of this target. Used for getting current position in `adjust`."""

    left: int
    """Left offset from parent widget"""

    right: int
    """Right offset from parent widget"""

    height: int
    """Total height"""

    top: int = 0
    """Top offset from parent widget"""

    _start: tuple[int, int] = field(init=False)
    _end: tuple[int, int] = field(init=False)

    onclick: Optional[MouseCallback] = None
    """Callback function for click events"""

    @property
    def start(self) -> tuple[int, int]:
        """Get start position"""

        return self._start

    @property
    def end(self) -> tuple[int, int]:
        """Get end position"""

        return self._end

    def adjust(self) -> None:
        """Adjust position to align with `parent`

        This should be called every time the parent's position might have changed."""

        pos = self.parent.pos
        self._start = (pos[0] + self.left - 1, pos[1] + 1 + self.top)
        self._end = (
            pos[0] + self.parent.width - 1 - self.right,
            pos[1] + self.top + self.height,
        )

    def contains(self, pos: tuple[int, int]) -> bool:
        """Check if `pos` is contained within the target area"""

        start = self._start
        end = self._end

        return start[0] <= pos[0] <= end[0] and start[1] <= pos[1] <= end[1]

    def click(self, caller: Widget) -> None:
        """Execute callback with self, caller as the argument"""

        if self.onclick is None:
            return

        self.onclick(self, caller)

    def show(self, color: Optional[int] = None) -> None:
        """Show target on screen with given color

        Note: This is only meant to be a debug function."""

        if color is None:
            color = 210

        for y_pos in range(self._start[1], self._end[1] + 1):
            with cursor_at((self._start[0], y_pos)) as print_here:
                length = self._end[0] - self._start[0]
                print_here(markup.parse(f"[@{color}]" + " " * length))


class Widget:
    """The base of the Widget system"""

    set_style = classmethod(_set_obj_or_cls_style)
    set_char = classmethod(_set_obj_or_cls_char)

    styles: dict[str, w_styles.StyleType] = {}
    """Default styles for this class"""

    chars: dict[str, w_styles.CharType] = {}
    """Default characters for this class"""

    keys: dict[str, set[str]] = {}
    """Groups of keys that are used in `handle_key`"""

    serialized: list[str] = [
        "id",
        "pos",
        "depth",
        "width",
        "height",
        "selected_index",
        "selectables_length",
    ]
    """Fields of widget that shall be serialized by `pytermgui.serializer.Serializer`"""

    # This class is loaded after this module,
    # and thus mypy doesn't see its existence.
    _id_manager: Optional["_IDManager"] = None  # type: ignore

    is_bindable = False
    """Allow binding support"""

    size_policy = SizePolicy.get_default()
    """`pytermgui.enums.SizePolicy` to set widget's width according to"""

    parent_align = HorizontalAlignment.get_default()
    """`pytermgui.enums.HorizontalAlignment` to align widget by"""

    def __init__(self, **attrs: Any) -> None:
        """Initialize object"""

        self.set_style = lambda key, value: _set_obj_or_cls_style(self, key, value)
        self.set_char = lambda key, value: _set_obj_or_cls_char(self, key, value)

        self.width = 1
        self.height = 1
        self.pos = terminal.origin

        self.depth = 0

        self.styles = type(self).styles.copy()
        self.chars = type(self).chars.copy()

        self.mouse_targets: list[MouseTarget] = []

        self.parent: Widget | None = None
        self.selected_index: int | None = None
        self.onclick: MouseCallback | None = None

        self._selectables_length = 0
        self._id: Optional[str] = None
        self._serialized_fields = type(self).serialized
        self._bindings: dict[str | Type[MouseEvent], tuple[BoundCallback, str]] = {}

        for attr, value in attrs.items():
            setattr(self, attr, value)

    def __repr__(self) -> str:
        """Return repr string of this widget.

        Returns:
            Whatever this widget's `debug` method gives.
        """

        return self.debug()

    def __iter__(self) -> Iterator[Widget]:
        """Return self for iteration"""

        yield self

    @property
    def bindings(self) -> dict[str | Type[MouseEvent], tuple[BoundCallback, str]]:
        """Gets a copy of the bindings internal dictionary.

        Returns:
            A copy of the internal bindings dictionary, such as:

            ```
            {
                "*": (star_callback, "This is a callback activated when '*' is pressed.")
            }
            ```
        """

        return self._bindings.copy()

    @property
    def id(self) -> Optional[str]:  # pylint: disable=invalid-name
        """Gets this widget's id property

        Returns:
            The id string if one is present, None otherwise.
        """

        return self._id

    @id.setter
    def id(self, value: str) -> None:  # pylint: disable=invalid-name
        """Registers a widget to the Widget._id_manager.

        If this widget already had an id, the old value is deregistered
        before the new one is assigned.

        Args:
            value: The new id this widget will be registered as.
        """

        if self._id == value:
            return

        manager = Widget._id_manager
        assert manager is not None

        old = manager.get_id(self)
        if old is not None:
            manager.deregister(old)

        self._id = value
        manager.register(self)

    @property
    def selectables_length(self) -> int:
        """Gets how many selectables this widget contains.

        Returns:
            An integer describing the amount of selectables in this widget.
        """

        return self._selectables_length

    @property
    def selectables(self) -> list[tuple[Widget, int]]:
        """Gets a list of all selectables within this widget

        Returns:
            A list of tuples. In the default implementation this will be
            a list of one tuple, containing a reference to `self`, as well
            as the lowest index, 0.
        """

        return [(self, 0)]

    @property
    def is_selectable(self) -> bool:
        """Determines whether this widget has any selectables.

        Returns:
            A boolean, representing `self.selectables_length != 0`.
        """

        return self.selectables_length != 0

    def static_width(self, value: int) -> None:
        """Sets this widget's width, and turns it static

        This method is just a shorter way of setting a new width, as well
        as changing the size_policy to `pytermgui.enums.SizePolicy.STATIC`.

        Args:
            value: The new width
        """

        self.width = value
        self.size_policy = SizePolicy.STATIC

    # Set static_width to a setter only property
    static_width = property(None, static_width)  # type: ignore

    def contains(self, pos: tuple[int, int]) -> bool:
        """Determines whether widget contains `pos`.

        Args:
            pos: Position to compare.

        Returns:
            Boolean describing whether the position is inside
              this widget.
        """

        rect = self.pos, (
            self.pos[0] + self.width,
            self.pos[1] + self.height,
        )

        (left, top), (right, bottom) = rect

        return left <= pos[0] < right and top <= pos[1] < bottom

    def define_mouse_target(
        self, left: int, right: int, height: int, top: int = 0
    ) -> MouseTarget:
        """Define a mouse target, return it for method assignments

        Note: Only use this within a `Widget`, preferably within its
        `get_lines()` method."""

        target = MouseTarget(self, left, right, height, top)

        target.adjust()
        self.mouse_targets.insert(0, target)

        return target

    def get_target(self, pos: tuple[int, int]) -> Optional[MouseTarget]:
        """Get MouseTarget for a position"""

        for target in self.mouse_targets:
            if target.contains(pos):
                return target

        return None

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Handles a mouse event, returning its success.

        Args:
            event: Object containing mouse event to handle.

        Returns:
            A boolean describing whether the mouse input was handled."""

        return False

    def handle_key(self, key: str) -> bool:
        """Handles a mouse event, returning its success.

        Args:
            key: String representation of input string.
              The `pytermgui.input.keys` object can be
              used to retrieve special keys.

        Returns:
            A boolean describing whether the key was handled.
        """

        return False and hasattr(self, key)

    def serialize(self) -> dict[str, Any]:
        """Serializes a widget.

        The fields looked at are defined `Widget.serialized`. Note that
        this method is not very commonly used at the moment, so it might
        not have full functionality in non-nuclear widgets.

        Returns:
            Dictionary of widget attributes. The dictionary will always
            have a `type` field. Any styles are converted into markup
            strings during serialization, so they can be loaded again in
            their original form.

            Example return:
            ```
                {
                    "type": "Label",
                    "value": "[210 bold]I am a title",
                    "parent_align": 0,
                    ...
                }
            ```
        """

        fields = self._serialized_fields

        out: dict[str, Any] = {"type": type(self).__name__}
        for key in fields:
            # Detect styled values
            if key.startswith("*"):
                style = True
                key = key[1:]
            else:
                style = False

            value = getattr(self, key)

            # Convert styled value into markup
            if style:
                style_call = self._get_style(key)
                if isinstance(value, list):
                    out[key] = [markup.get_markup(style_call(char)) for char in value]
                else:
                    out[key] = markup.get_markup(style_call(value))

                continue

            out[key] = value

        # The chars need to be handled separately
        out["chars"] = {}
        for key, value in self.chars.items():
            style_call = self._get_style(key)

            if isinstance(value, list):
                out["chars"][key] = [
                    markup.get_markup(style_call(char)) for char in value
                ]
            else:
                out["chars"][key] = markup.get_markup(style_call(value))

        return out

    def copy(self) -> Widget:
        """Creates a deep copy of this widget"""

        return deepcopy(self)

    def _get_style(self, key: str) -> w_styles.DepthlessStyleType:
        """Gets style call from its key.

        Args:
            key: A key into the widget's styles dictionary.

        Returns:
            A `pytermgui.styles.StyleCall` object containing the referenced
            style. StyleCall objects should only be used internally inside a
            widget.

        Raises:
            KeyError: Style key is invalid.
        """

        style_method = self.styles[key]

        return w_styles.StyleCall(self, style_method)

    def _get_char(self, key: str) -> w_styles.CharType:
        """Gets character from its key.

        Args:
            key: A key into the widget's chars dictionary.

        Returns:
            Either a `list[str]` or a simple `str`, depending on the character.

        Raises:
            KeyError: Style key is invalid.
        """

        chars = self.chars[key]
        if isinstance(chars, str):
            return chars

        return chars.copy()

    def get_lines(self) -> list[str]:
        """Gets lines representing this widget.

        These lines have to be equal to the widget in length. All
        widgets must provide this method. Make sure to keep it performant,
        as it will be called very often, often multiple times per WindowManager frame.

        Any longer actions should be done outside of this method, and only their
        result should be looked up here.

        Returns:
            Nothing by default.

        Raises:
            NotImplementedError: As this method is required for **all** widgets, not
                having it defined will raise NotImplementedError.
        """

        raise NotImplementedError(f"get_lines() is not defined for type {type(self)}.")

    def bind(
        self, key: str, action: BoundCallback, description: Optional[str] = None
    ) -> None:
        """Binds an action to a keypress.

        This function is only called by implementations above this layer. To use this
        functionality use `pytermgui.window_manager.WindowManager`, or write your own
        custom layer.

        Special keys:
        - keys.ANY_KEY: Any and all keypresses execute this binding.
        - keys.MouseAction: Any and all mouse inputs execute this binding.

        Args:
            key: The key that the action will be bound to.
            action: The action executed when the key is pressed.
            description: An optional description for this binding. It is not really
                used anywhere, but you can provide a helper menu and display them.

        Raises:
            TypeError: This widget is not bindable, i.e. widget.is_bindable == False.
        """

        if not self.is_bindable:
            raise TypeError(f"Widget of type {type(self)} does not accept bindings.")

        if description is None:
            description = f"Binding of {key} to {action}"

        self._bindings[key] = (action, description)

    def execute_binding(self, key: Any) -> bool:
        """Executes a binding belonging to key, when present.

        Use this method inside custom widget `handle_keys` methods, or to run a callback
        without its corresponding key having been pressed.

        Args:
            key: Usually a string, indexing into the `_bindings` dictionary. These are the
              same strings as defined in `Widget.bind`.

        Returns:
            True if the binding was found, False otherwise. Bindings will always be
              executed if they are found.
        """

        # Execute special binding
        if keys.ANY_KEY in self._bindings:
            method, _ = self._bindings[keys.ANY_KEY]
            method(self, key)

        if key in self._bindings:
            method, _ = self._bindings[key]
            method(self, key)

            return True

        return False

    def select(self, index: int | None = None) -> None:
        """Selects a part of this Widget.

        Args:
            index: The index to select.

        Raises:
            TypeError: This widget has no selectables, i.e. widget.is_selectable == False.
        """

        if not self.is_selectable:
            raise TypeError(f"Object of type {type(self)} has no selectables.")

        if index is not None:
            index = min(max(0, index), self.selectables_length - 1)
        self.selected_index = index

    def print(self) -> None:
        """Prints this widget"""

        for line in self.get_lines:
            print(line)

    def debug(self) -> str:
        """Returns identifiable information about this widget.

        This method is used to easily differentiate between widgets. By default, all widget's
        __repr__ method is an alias to this. The signature of each widget is used to generate
        the return value.

        Returns:
            A string almost exactly matching the line of code that could have defined the widget.

            Example return:

            ```
            Container(Label(value="This is a label", padding=0), Button(label="This is a button", padding=0), **attrs)
            ```

        """

        constructor = "("
        for name in signature(getattr(self, "__init__")).parameters:
            current = ""
            if name == "attrs":
                current += "**attrs"
                continue

            if len(constructor) > 1:
                current += ", "

            current += name

            attr = getattr(self, name, None)
            if attr is None:
                continue

            current += "="

            if isinstance(attr, str):
                current += f'"{attr}"'
            else:
                current += str(attr)

            constructor += current

        constructor += ")"

        return type(self).__name__ + constructor


class Container(Widget):
    """A widget that contains other widgets."""

    chars: dict[str, w_styles.CharType] = {
        "border": ["| ", "-", " |", "-"],
        "corner": [""] * 4,
    }

    styles = {
        "border": w_styles.MARKUP,
        "corner": w_styles.MARKUP,
        "fill": w_styles.BACKGROUND,
    }

    keys = {
        "next": {keys.DOWN, keys.CTRL_N, "j"},
        "previous": {keys.UP, keys.CTRL_P, "k"},
    }

    serialized = Widget.serialized + ["_centered_axis"]
    vertical_align = VerticalAlignment.MIDDLE
    allow_fullscreen = True

    # TODO: Add `WidgetConvertible`? type instead of Any
    def __init__(self, *widgets: Any, **attrs: Any) -> None:
        """Initialize Container data"""

        super().__init__(**attrs)

        # TODO: This is just a band-aid.
        if "width" not in attrs:
            self.width = 40

        self._widgets: list[Widget] = []
        self._centered_axis: CenteringPolicy | None = None

        self._prev_screen: tuple[int, int] = (0, 0)
        self._has_printed = False

        self.styles = type(self).styles.copy()
        self.chars = type(self).chars.copy()

        for widget in widgets:
            self._add_widget(widget)

        self._drag_target: Widget | None = None
        terminal.subscribe(terminal.RESIZE, lambda *_: self.center(self._centered_axis))

    @property
    def sidelength(self) -> int:
        """Gets the length of left and right borders combined.

        Returns:
            An integer equal to the `pytermgui.helpers.real_length` of the concatenation of
                the left and right borders of this widget, both with their respective styles
                applied.
        """

        chars = self._get_char("border")
        style = self._get_style("border")
        if not isinstance(chars, list):
            return 0

        left_border, _, right_border, _ = chars
        return real_length(style(left_border) + style(right_border))

    @property
    def selectables(self) -> list[tuple[Widget, int]]:
        """Gets all selectable widgets and their inner indices.

        This is used in order to have a constant reference to all selectable indices within this
        widget.

        Returns:
            A list of tuples containing a widget and an integer each. For each widget that is
            withing this one, it is added to this list as many times as it has selectables. Each
            of the integers correspond to a selectable_index within the widget.

            For example, a Container with a Button, InputField and an inner Container containing
            3 selectables might return something like this:

            ```
            [
                (Button(...), 0),
                (InputField(...), 0),
                (Container(...), 0),
                (Container(...), 1),
                (Container(...), 2),
            ]
            ```
        """

        _selectables: list[tuple[Widget, int]] = []
        for widget in self._widgets:
            if not widget.is_selectable:
                continue

            for i, (inner, _) in enumerate(widget.selectables):
                _selectables.append((inner, i))

        return _selectables

    @property
    def selectables_length(self) -> int:
        """Gets the length of the selectables list.

        Returns:
            An integer equal to the length of `self.selectables`.
        """

        return len(self.selectables)

    @property
    def selected(self) -> Optional[Widget]:
        """Returns the currently selected object

        Returns:
            The currently selected widget if selected_index is not None,
            otherwise None.
        """

        # TODO: Add deeper selection

        if self.selected_index is None:
            return None

        if self.selected_index >= len(self.selectables):
            return None

        return self.selectables[self.selected_index][0]

    @property
    def box(self) -> boxes.Box:
        """Returns current box setting

        Returns:
            The currently set box instance.
        """

        return self._box

    @box.setter
    def box(self, new: str | boxes.Box) -> None:
        """Applies a new box.

        Args:
            new: Either a `pytermgui.boxes.Box` instance or a string
                analogous to one of the default box names.
        """

        if isinstance(new, str):
            from_module = vars(boxes).get(new)
            if from_module is None:
                raise ValueError(f"Unknown box type {new}.")

            new = from_module

        assert isinstance(new, boxes.Box)
        self._box = new
        new.set_chars_of(self)

    def __iadd__(self, other: object) -> Container:
        """Adds a new widget, then returns self.

        Args:
            other: Any widget instance, or data structure that can be turned
            into a widget by `Widget.from_data`.

        Returns:
            A reference to self.
        """

        self._add_widget(other)
        return self

    def __add__(self, other: object) -> Container:
        """Adds a new widget, then returns self.

        This method is analogous to `Container.__iadd__`.

        Args:
            other: Any widget instance, or data structure that can be turned
            into a widget by `Widget.from_data`.

        Returns:
            A reference to self.
        """

        self.__iadd__(other)
        return self

    def __iter__(self) -> Iterator[Widget]:
        """Gets an iterator of self._widgets.

        Yields:
            The next widget.
        """

        for widget in self._widgets:
            yield widget

    def __len__(self) -> int:
        """Gets the length of the widgets list.

        Returns:
            An integer describing len(self._widgets).
        """

        return len(self._widgets)

    def __getitem__(self, sli: int | slice) -> Widget | list[Widget]:
        """Gets an item from self._widgets.

        Args:
            sli: Slice of the list.

        Returns:
            The slice in the list.
        """

        return self._widgets[sli]

    def __setitem__(self, index: int, value: Any) -> None:
        """Sets an item in self._widgets.

        Args:
            index: The index to be set.
            value: The new widget at this index.
        """

        self._widgets[index] = value

    def __contains__(self, other: object) -> bool:
        """Determines if self._widgets contains other widget.

        Args:
            other: Any widget-like.

        Returns:
            A boolean describing whether `other` is in `self.widgets`
        """

        return other in self._widgets

    def _add_widget(self, other: object, run_get_lines: bool = True) -> None:
        """Adds other to this widget.

        Args:
            other: Any widget-like object.
            run_get_lines: Boolean controlling whether the self.get_lines is ran.
        """

        if not isinstance(other, Widget):
            to_widget = Widget.from_data(other)
            if to_widget is None:
                raise ValueError(
                    f"Could not convert {other} of type {type(other)} to a Widget!"
                )

            other = to_widget

        # This is safe to do, as it would've raised an exception above already
        assert isinstance(other, Widget)

        self._widgets.append(other)
        if isinstance(other, Container):
            other.set_recursive_depth(self.depth + 2)
        else:
            other.depth = self.depth + 1

        other.get_lines()
        other.parent = self

        if run_get_lines:
            self.get_lines()

    def _get_aligners(
        self, widget: Widget, borders: tuple[str, str]
    ) -> tuple[Callable[[str], str], int]:
        """Gets an aligning method and position offset.

        Args:
            widget: The widget to align.
            borders: The left and right borders to put the widget within.

        Returns:
            A tuple of a method that, when called with a line, will return that line
            centered using the passed in widget's parent_align and width, as well as
            the horizontal offset resulting from the widget being aligned.
        """

        left, right = borders
        char = self._get_style("fill")(" ")

        def _align_left(text: str) -> str:
            """Align line to the left"""

            padding = self.width - real_length(left + right) - real_length(text)
            return left + text + padding * char + right

        def _align_center(text: str) -> str:
            """Align line to the center"""

            total = self.width - real_length(left + right) - real_length(text)
            padding, offset = divmod(total, 2)
            return left + (padding + offset) * char + text + padding * char + right

        def _align_right(text: str) -> str:
            """Align line to the right"""

            padding = self.width - real_length(left + right) - real_length(text)
            return left + padding * char + text + right

        if widget.parent_align == HorizontalAlignment.CENTER:
            total = self.width - real_length(left + right) - widget.width
            padding, offset = divmod(total, 2)
            return _align_center, real_length(left) + padding + offset

        if widget.parent_align == HorizontalAlignment.RIGHT:
            return _align_right, self.width - real_length(left) - widget.width

        # Default to left-aligned
        return _align_left, real_length(left)

    def _update_width(self, widget: Widget) -> None:
        """Updates the width of widget or self.

        This method respects widget.size_policy.

        Args:
            widget: The widget to update/base updates on.
        """

        available = (
            self.width - self.sidelength - (0 if isinstance(widget, Container) else 1)
        )

        if widget.size_policy == SizePolicy.FILL:
            widget.width = available
            return

        if widget.size_policy == SizePolicy.RELATIVE:
            widget.width = widget.relative_width * available
            return

        if widget.width > available:
            if widget.size_policy == SizePolicy.STATIC:
                raise WidthExceededError(
                    f"Widget {widget}'s static width of {widget.width}"
                    + f" exceeds its parent's available width {available}."
                    ""
                )

            widget.width = available

    def _apply_vertalign(
        self, lines: list[str], diff: int, padder: str
    ) -> tuple[int, list[str]]:
        """Insert padder line into lines diff times, depending on self.vertical_align.

        Args:
            lines: The list of lines to align.
            diff: The available height.
            padder: The line to use to pad.

        Returns:
            A tuple containing the vertical offset as well as the padded list of lines.

        Raises:
            NotImplementedError: The given vertical alignment is not implemented.
        """

        if self.vertical_align == VerticalAlignment.BOTTOM:
            for _ in range(diff):
                lines.insert(0, padder)

            return diff, lines

        if self.vertical_align == VerticalAlignment.TOP:
            for _ in range(diff):
                lines.append(padder)

            return 0, lines

        if self.vertical_align == VerticalAlignment.MIDDLE:
            top, extra = divmod(diff, 2)
            bottom = top + extra

            for _ in range(top):
                lines.insert(0, padder)

            for _ in range(bottom):
                lines.append(padder)

            return top, lines

        raise NotImplementedError(
            f"Vertical alignment {self.vertical_align} is not implemented for {type(self)}."
        )

    def get_lines(self) -> list[str]:
        """Gets all lines by spacing out inner widgets.

        This method reflects & applies both width settings, as well as
        the `parent_align` field.

        Returns:
            A list of all lines that represent this Container.
        """

        def _get_border(left: str, char: str, right: str) -> str:
            """Gets a top or bottom border.

            Args:
                left: Left corner character.
                char: Border character filling between left & right.
                right: Right corner character.

            Returns:
                The border line.
            """

            offset = real_length(left + right)
            return left + char * (self.width - offset) + right

        lines = []

        style = self._get_style("border")
        borders = [style(char) for char in self._get_char("border")]

        style = self._get_style("corner")
        corners = [style(char) for char in self._get_char("corner")]

        has_top_bottom = (real_length(borders[1]) > 0, real_length(borders[3]) > 0)

        baseline = 0
        align = lambda item: item

        for widget in self._widgets:
            align, offset = self._get_aligners(widget, (borders[0], borders[2]))

            self._update_width(widget)

            widget.pos = (
                self.pos[0] + offset,
                self.pos[1] + len(lines) + (1 if has_top_bottom[0] else 0),
            )

            widget_lines = []
            for line in widget.get_lines():
                widget_lines.append(align(line))

            lines.extend(widget_lines)

        vertical_offset, lines = self._apply_vertalign(
            lines, self.height - len(lines) - sum(has_top_bottom), align("")
        )

        for widget in self._widgets:
            widget.pos = (widget.pos[0], widget.pos[1] + vertical_offset)

            # TODO: This is wasteful.
            widget.get_lines()

        if has_top_bottom[0]:
            lines.insert(0, _get_border(corners[0], borders[1], corners[1]))

        if has_top_bottom[1]:
            lines.append(_get_border(corners[3], borders[3], corners[2]))

        self.height = len(lines)
        return lines

    def set_widgets(self, new: list[Widget]) -> None:
        """Sets new list in place of self._widgets.

        Args:
            new: The new widget list.
        """

        self._widgets = []
        for widget in new:
            self._add_widget(widget)

    def serialize(self) -> dict[str, Any]:
        """Serializes this Container, adding in serializations of all widgets.

        See `pytermgui.widgets.base.Widget.serialize` for more info.

        Returns:
            The dictionary containing all serialized data.
        """

        out = super().serialize()
        out["_widgets"] = []

        for widget in self._widgets:
            out["_widgets"].append(widget.serialize())

        return out

    def pop(self, index: int = -1) -> Widget:
        """Pops widget from self._widgets.

        Analogous to self._widgets.pop(index).

        Args:
            index: The index to operate on.

        Returns:
            The widget that was popped off the list.
        """

        return self._widgets.pop(index)

    def remove(self, other: Widget) -> None:
        """Remove widget from self._widgets

        Analogous to self._widgets.remove(other).

        Args:
            widget: The widget to remove.
        """

        return self._widgets.remove(other)

    def set_recursive_depth(self, value: int) -> None:
        """Set depth for this Container and all its children.

        All inner widgets will receive value+1 as their new depth.

        Args:
            value: The new depth to use as the base depth.
        """

        self.depth = value
        for widget in self._widgets:
            if isinstance(widget, Container):
                widget.set_recursive_depth(value + 1)
            else:
                widget.depth = value

    def select(self, index: int | None = None) -> None:
        """Selects inner subwidget.

        Args:
            index: The index to select.

        Raises:
            IndexError: The index provided was beyond len(self.selectables).
        """

        # Unselect all sub-elements
        for other in self._widgets:
            if other.selectables_length > 0:
                other.select(None)

        if index is not None:
            if index >= len(self.selectables) is None:
                raise IndexError("Container selection index out of range")

            widget, inner_index = self.selectables[index]
            widget.select(inner_index)

        self.selected_index = index

    def center(
        self, where: CenteringPolicy | None = None, store: bool = True
    ) -> Container:
        """Centers this object to the given axis.

        Args:
            where: A CenteringPolicy describing the place to center to
            store: When set, this centering will be reapplied during every
                print, as well as when calling this method with no arguments.

        Returns:
            This Container.
        """

        # Refresh in case changes happened
        self.get_lines()

        if where is None:
            # See `enums.py` for explanation about this ignore.
            where = CenteringPolicy.get_default()  # type: ignore

        centerx = centery = where is CenteringPolicy.ALL
        centerx |= where is CenteringPolicy.HORIZONTAL
        centery |= where is CenteringPolicy.VERTICAL

        pos = list(self.pos)
        if centerx:
            pos[0] = (terminal.width - self.width + 2) // 2

        if centery:
            pos[1] = (terminal.height - self.height + 2) // 2

        self.pos = (pos[0], pos[1])

        if store:
            self._centered_axis = where

        self._prev_screen = terminal.size

        return self

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Applies a mouse event on all children.

        Args:
            event: The event to handle

        Returns:
            A boolean showing whether the event was handled.
        """

        if event.action is MouseAction.RELEASE:
            self._drag_target = None

        if self._drag_target is not None:
            return self._drag_target.handle_mouse(event)

        selectables_index = 0
        for widget in self._widgets:
            if widget.contains(event.position):
                if event.action is MouseAction.LEFT_CLICK:
                    self._drag_target = widget
                    self.select(selectables_index)

                if widget.handle_mouse(event):
                    break

            if widget.is_selectable:
                selectables_index += 1

        return False

    def handle_key(self, key: str) -> bool:
        """Handles a keypress, returns its success.

        Args:
            key: A key str.

        Returns:
            A boolean showing whether the key was handled.
        """

        def _is_nav(key: str) -> bool:
            """Determine if a key is in the navigation sets"""

            return key in self.keys["next"] | self.keys["previous"]

        if self.selected is not None and self.selected.handle_key(key):
            return True

        # Only use navigation when there is more than one selectable
        if self.selectables_length > 1 and _is_nav(key):
            handled = False
            if self.selected_index is None:
                self.select(0)

            assert isinstance(self.selected_index, int)

            if key in self.keys["previous"]:
                # No more selectables left, user wants to exit Container
                # upwards.
                if self.selected_index == 0:
                    return False

                self.select(self.selected_index - 1)
                handled = True

            elif key in self.keys["next"]:
                # Stop selection at last element, return as unhandled
                new = self.selected_index + 1
                if new == len(self.selectables):
                    return False

                self.select(new)
                handled = True

            if handled:
                return True

        if key == keys.ENTER and self.selected is not None:
            if self.selected.selected_index is not None:
                self.selected.handle_key(key)
                return True

        return False

    def wipe(self) -> None:
        """Wipes the characters occupied by the object"""

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(real_length(line) * " ")

    def print(self) -> None:
        """Prints this Container.

        If the screen size has changed since last `print` call, the object
        will be centered based on its `_centered_axis`.
        """

        if not terminal.size == self._prev_screen:
            clear()
            self.center(self._centered_axis)

        self._prev_screen = terminal.size

        if self.allow_fullscreen:
            self.pos = terminal.origin

        with cursor_at(self.pos) as print_here:
            for line in self.get_lines():
                print_here(line)

        self._has_printed = True

    def debug(self) -> str:
        """Returns a string with identifiable information on this widget.

        Returns:
            A str in the form of a class construction. This string is in a form that
            __could have been__ used to create this Container.
        """

        out = "Container("
        for widget in self._widgets:
            out += widget.debug() + ", "

        out = out.strip(", ")
        out += ", **attrs)"

        return out


class Label(Widget):
    """A Widget to display a string

    By default, this widget uses `pytermgui.widgets.styles.MARKUP`. This
    allows it to house markup text that is parsed before display, such as:

    ```python3
    import pytermgui as ptg

    with ptg.alt_buffer():
        root = ptg.Container(
            ptg.Label("[italic 141 bold]This is some [green]fancy [white inverse]text!")
        )
        root.print()
        ptg.getch()
    ```

    <p style="text-align: center">
     <img
      src="https://github.com/bczsalba/pytermgui/blob/master/assets/docs/widgets/label.png?raw=true"
      width=100%>
    </p>
    """

    styles: dict[str, w_styles.StyleType] = {"value": w_styles.MARKUP}

    serialized = Widget.serialized + ["*value", "align", "padding"]

    def __init__(self, value: str = "", padding: int = 0, **attrs: Any) -> None:
        """Set up object"""

        super().__init__(**attrs)

        self.value = value
        self.padding = padding
        self.width = real_length(value) + self.padding

    def get_lines(self) -> list[str]:
        """Get lines representing this Label, breaking lines as necessary"""

        value_style = self._get_style("value")
        line_gen = break_line(value_style(self.padding * " " + self.value), self.width)

        return list(line_gen) or [""]
