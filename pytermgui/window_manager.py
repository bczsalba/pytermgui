"""
pytermgui.window_manager
------------------------
author: bczsalba


This module contains a full implementation of a traditional window manager,
right inside your terminal.

It has no outside dependencies, only depends on the rest of pytermgui. There is full mouse support,
including moving windows by dragging their top borders, clicking buttons inside windows and resizing
windows by dragging their right borders.

Inspired by https://github.com/epiclabs-io/winman.

Notes:
    - Instead of Container-s, this module uses Window-s, which are essentially Container++
    - Window-s can have some special types:
        + static: Non-draggable
        + modal: Forced as 0th focus item, focus cannot be changed as long as the Window is alive.

Example:
    >>> from pytermgui import WindowManager, Window, DebugWindow
    >>> manager = WindowManager()
    >>> manager.add(DebugWindow())
    >>> manager.run()
"""

# These object need more than 7 attributes.
# pylint: disable=too-many-instance-attributes

from __future__ import annotations

import sys
from time import time
from random import randint
from enum import Enum, auto as _auto
from typing import Optional, Callable, Any, cast

# https://github.com/python/mypy/issues/4930
from .widgets.base import Container

from .widgets import (
    MouseCallback,
    MouseTarget,
    InputField,
    Widget,
    Button,
    Label,
    boxes,
)

from .input import getch, keys
from .parser import define_tag, ansi
from .exceptions import LineLengthError
from .helpers import real_length, strip_ansi
from .context_managers import alt_buffer, mouse_handler, MouseEvent
from .ansi_interface import clear, screen_size, screen_width, MouseAction


__all__ = [
    "Window",
    "WindowManager",
    "DebugWindow",
    "MouseDebugger",
    "WindowDebugger",
]


class Edge(Enum):
    """Enum for window edges"""

    LEFT = _auto()
    TOP = _auto()
    RIGHT = _auto()
    BOTTOM = _auto()


class Window(Container):
    """Essentially Container++"""

    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3

    chars = Container.chars | {"button": ["<", ">"]}

    def __init__(
        self,
        static: bool = False,
        modal: bool = False,
        resizable: bool = True,
        title: str = "",
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)
        self._is_bindable = True

        self.is_static: bool = static
        self.is_modal: bool = modal
        self.is_resizable: bool = resizable
        self.manager: Optional["WindowManager"] = None

        self.min_width: Optional[int] = None
        self.is_force_focus: bool = False

        self._target: Optional[MouseTarget] = None
        self._previous_mouse: Optional[tuple[int, int]] = None

        self._is_full_screen: bool = False
        self._restore_size: tuple[int, int] = (self.width, self.height)
        self._restore_pos: tuple[int, int] = self.pos
        self._toolbar_buttons: list[MouseTarget] = []

        self.set_title(title)
        self.safe_state: Optional[tuple[int, Optional[int]]] = None

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """Get rectangle of Window"""

        posx, posy = self.pos
        return posx, posy, posx + self.width - 1, posy + self.height - 1

    @rect.setter
    def rect(self, new: tuple[int, int, int, int]) -> None:
        """Set new rectangle of Window"""

        width, height = screen_size()
        startx, starty, endx, endy = new
        startx = max(0, min(startx, width))
        starty = max(0, min(starty, height))
        self.pos = (startx, starty)

        self.forced_width = endx - startx
        self.forced_height = endy - starty

    def set_title(self, title: str) -> None:
        """Set top-left title string"""

        self.title = title
        corners = self.get_char("corner")
        assert len(corners) == 4 and isinstance(corners, list)
        corners[0] += title
        self.set_char("corner", corners)

    def close(self) -> None:
        """Instruct manager to close this window"""

        assert self.manager is not None
        self.manager.close(self)

    def change_align(self, new: int) -> None:
        """Change all widgets' parent_align"""

        for widget in self._widgets:
            widget.parent_align = new

    def notify(self, event: Any) -> bool:
        """Notify window of an event"""

        return not (self or event)

    def contains(self, pos: tuple[int, int]) -> bool:
        """Return if self.rec contains pos"""

        startx, starty, endx, endy = self.rect
        return startx <= pos[0] <= endx and starty <= pos[1] <= endy

    def get_target(self, pos: tuple[int, int]) -> Optional[MouseTarget]:
        """Get target at position"""

        for target in self.mouse_targets:
            if target.contains(pos):
                return target

        return None

    def add_button(self, text: str, position: int = TOP_RIGHT) -> MouseTarget:
        """Add a MouseTarget to either corner, return it"""

        # TODO: Something wong, resize breaks this.

        corners = self.get_char("corner")
        assert isinstance(corners, list) and len(corners) == 4

        delimiters = self.get_char("button")
        assert len(delimiters) == 2 and isinstance(delimiters, list)
        start, end = delimiters

        current_length = real_length(corners[position])

        if position % 2 == 0:
            left = current_length + real_length(start)
            right = self.width
            corners[position] += start + text + end

        else:
            left = self.width - current_length - 1
            right = current_length + real_length(start) + 1
            corners[position] = start + text + end + corners[position]

        target = self.define_mouse_target(left=left, right=right, top=-1, height=1)
        target.adjust()

        self._toolbar_buttons.append(target)
        self.set_char("corner", corners)

        return target

    def handle_mouse(self, action: MouseAction, pos: tuple[int, int]) -> bool:
        """Handle a key string, WITHOUT looping"""

    def handle_key(self, key: str) -> bool:
        """Handle mouse press, WITHOUT looping"""

        if self.execute_binding(key):
            return True

        self.selected: Widget

        if isinstance(self.selected, InputField):


            if self.selected.send(key):
                assert self.manager is not None
                self.manager.print()
                return True

        if len(self._selectables) == 0:
            return False

        self.selected_index: Optional[int]
        if self.selected_index is None:
            self.selected_index = 0

        if key in [keys.UP, keys.CTRL_P, "k"]:
            self.selected_index -= 1

        elif key in [keys.DOWN, keys.CTRL_N, "j"]:
            self.selected_index += 1

        elif key == keys.RETURN:
            if self.selected_index is None:
                return False

            widget, inner_index = self._selectables[self.selected_index]
            self.click(widget.mouse_targets[inner_index].start)

        else:
            return False

        self.select()
        return True

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen of a Window"""

        for widget in self._widgets:
            widget.forced_width = None

        if not self._is_full_screen:
            self._restore_size = self.width, self.height
            self._restore_pos = self.pos
            width, height = screen_size()
            pos = (1, 1)

        else:
            width, height = self._restore_size
            height -= 2
            pos = self._restore_pos

        for widget in self._widgets:
            widget.forced_width = None

        self.forced_width = width
        self.forced_height = height
        self.pos = pos

        # TODO: Add a widget flag to "track" parent width
        inner_width = width - self.sidelength - 1

        self._is_full_screen ^= True

        for widget in self._widgets:
            widget.width = inner_width
            for target in self.mouse_targets:
                target.adjust()


class WindowManager(Container):
    """A manager for Window objects

    This class works similarly (in principle, at least) to a
    desktop WM. You add Windows to it, which can then be moved, resized
    and interacted with, all facilitated by the WindowManager object.

    The object gets activated by calling its `run()` method, which handles every
    aforementioned action. Pressing CTRL_C will call the manager's `exit()` method,
    which can return True (default) to break input loop.
    """

    styles = {"blurred": lambda _, item: ansi("[240]" + strip_ansi(item))}

    def __init__(self, *windows: Window) -> None:
        """Initialize object"""

        super().__init__()
        self._is_bindable = True
        self._windows: list[Window] = []
        self._mouse_listener: Optional[Window] = None

        define_tag("wm-title", "210 bold")
        define_tag("wm-section", "157")

        for window in windows:
            self.add(window)

        self._focus_index = 0
        self._drag_target: Optional[Window] = None
        self._drag_edge: Optional[Edge] = None
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0
        self._is_stopped: bool = False

        self.mouse_handler: Optional[Callable[[str], Optional[list[MouseEvent]]]] = None

    def __enter__(self) -> WindowManager:
        """Start context manager"""

        return self

    def __exit__(self, _: Any, exception: Exception, __: Any) -> bool:
        """End context manager"""

        if exception is not None:
            raise exception

        self.stop()
        return True

    def _click_or_init_drag(self, pos: tuple[int, int]) -> bool:
        """Initialize data for dragging a window"""

        for window in self._windows:
            if window.contains(pos):
                self.focus_window(window)

                # We clicked a non-button area
                if window.click(pos) is None:
                    window.selected_index = None
                    self._drag_edge = self._get_edge(window, pos)

                    if self._drag_edge is None:
                        return False

                    self._drag_target = window
                    self._drag_offset_x = pos[0] - window.pos[0]
                    self._drag_offset_y = pos[1] - window.pos[1]

                break

            # Stop if a modal window was found
            if window.is_modal:
                break

        return True

    @staticmethod
    def _get_edge(window: Window, pos: tuple[int, int]) -> Optional[Edge]:
        """Get which edge mouse input overlaps with"""

        startx, starty, endx, endy = window.rect

        if pos[0] == startx:
            return Edge.LEFT

        if pos[0] == endx:
            return Edge.RIGHT

        if pos[1] == starty:
            return Edge.TOP

        if pos[1] == endy:
            return Edge.BOTTOM

        return None

    @staticmethod
    def get_root(widget: Widget) -> Widget:
        """Get root widget"""

        while hasattr(widget, "parent"):
            widget = widget.parent

        return widget

    @property
    def focused(self) -> Optional[Window]:
        """Return currently focused window"""

        if len(self._windows) > 0:
            return self._windows[0]

        return None

    def align_widgets(self, new: int) -> None:
        """Set all widgets' parent_align"""

        for widget in self._widgets:
            widget.parent_align = new

    def set_mouse_listener(self, window: Window) -> None:
        """Allow window to recieve mouse events"""

        self._mouse_listener = window

    def focus_window(self, window: Window) -> None:
        """Focus window"""

        self._windows.pop(self._windows.index(window))
        self._windows.insert(0, window)

    def get_target(self, pos: tuple[int, int]) -> Optional[MouseTarget]:
        """Get target at position"""

        for window in self._windows:
            target = window.get_target(pos)
            if isinstance(target, MouseTarget):
                return target

        return None

    def blur(self) -> None:
        """Blur all windows"""

        for window in self._windows:
            window.blur()

    def add(self, window: Window) -> None:
        """Add new window"""

        self._windows.insert(0, window)

        window.manager = self
        window.creation = time()
        if window.selectables_length > 0:
            window.select(0)

    def click(self, pos: tuple[int, int]) -> Optional[MouseTarget]:
        """Override click method to use windows"""

        for window in self._windows:
            target = window.click(pos)
            if target is not None:
                return target

            # Don't pass-through clicks
            if (
                window.pos[0] <= pos[0] <= window.pos[0] + window.width
                and window.pos[1] <= pos[1] <= window.pos[1] + window.height
            ):
                return None

        return None

    def close(self, window: Window) -> None:
        """Close a window"""

        self._windows.remove(window)
        self.print()

    def handle_key(self, key: str) -> bool:
        """Handle a keypress

        Note: This is called by the run loop on every iteration."""

        if self.execute_binding(key):
            return True

        if (
            key == keys.ALT + keys.TAB
            and self.focused is not None
            and not self.focused.is_modal
        ):
            self._focus_index += 1
            if self._focus_index >= len(self._windows):
                self._focus_index = 0

            self.focus_window(
                sorted(self._windows, key=lambda window: (window.creation))[  # type: ignore
                    self._focus_index
                ]
            )

        return False

    def handle_mouse(self, mouse_events: Optional[list[Optional[MouseEvent]]]) -> bool:
        """Handle a possible list of mouse events

        Note: This is called by the run loop on every iteration."""

        if mouse_events is None:
            return False

        for event in mouse_events:
            if event is None or (
                self._mouse_listener is not None and self._mouse_listener.notify(event)
            ):
                continue

            action, pos = event

            # Try clicking a Window, else try initializing dragging
            if action is MouseAction.PRESS:
                self._click_or_init_drag(pos)
                continue

            # Reset drag data
            if action is MouseAction.RELEASE:
                self._drag_target = None
                continue

            # Move or resize windows
            if action is MouseAction.HOLD and self._drag_target is not None:
                width, height = screen_size()
                window = self._drag_target

                startx, starty, _, endy = window.rect

                # Move window
                if self._drag_edge is Edge.TOP and not window.is_static:
                    newx = max(
                        0, min(pos[0] - self._drag_offset_x, width - window.width)
                    )
                    newy = max(
                        0, min(pos[1] - self._drag_offset_y, height - window.height)
                    )

                    window.pos = (newx, newy)

                # Change window width
                elif self._drag_edge is Edge.RIGHT and window.is_resizable:
                    if window.min_width is not None:
                        if pos[0] - startx < window.min_width:
                            return False

                    window.rect = startx, starty, pos[0], endy - 2

        return True

    def run(self) -> None:
        """Run window manager"""

        with mouse_handler("press_hold", "decimal_urxvt") as mouse:
            # This is set so this method is accessible from the outside
            self.mouse_handler = mouse

            with alt_buffer(echo=False, cursor=False):
                self.print()

                while True:
                    if self._is_stopped:
                        break

                    key = getch(interrupts=False)

                    if key == chr(3):
                        if self.exit(self):
                            break

                    events = mouse(key)

                    if not key == keys.ESC and self.handle_mouse(events):
                        self.print()
                        continue

                    if self.focused is not None and self.focused.handle_key(key):
                        self.print()
                        continue

                    if self.handle_key(key):
                        self.print()

    def stop(self) -> None:
        """Stop window manager"""

        self._is_stopped = True

    def print(self) -> None:
        """Print all windows"""

        def get_pos(window: Container, offset: int) -> str:
            """Get position"""

            new = list(window.pos)
            new[1] += offset

            return f"\033[{new[1]};{new[0]}H"

        buff = ""
        blurred_style = self.get_style("blurred")

        for i, window in enumerate(reversed(self._windows)):
            try:
                lines = window.get_lines()
            except LineLengthError as error:
                if window.safe_state is None:
                    raise ValueError("No safe fallback state") from error

                # Fall back to previously known safe-state
                # TODO: This is temporary! Somehow widgets
                #       can get updated quicker than they
                #       can react to? It's quite odd.
                width, f_width = window.safe_state

                if window.forced_width is not None:
                    window.forced_width = f_width
                else:
                    window.width = width

                try:
                    lines = window.get_lines()
                except LineLengthError:
                    continue

            window.safe_state = window.width, window.forced_width

            if i == len(self._windows) - 1 or window.is_force_focus:
                for lineindex, line in enumerate(lines):
                    buff += get_pos(window, lineindex) + line

            else:
                for lineindex, line in enumerate(lines):
                    buff += get_pos(window, lineindex) + blurred_style(line)

        clear()
        sys.stdout.write(buff)
        sys.stdout.flush()

    def show_targets(self, color: Optional[int] = None) -> None:
        """Show all targets"""

        for window in self._windows:
            window.show_targets(color)

        getch()
        self.print()

    @staticmethod
    def exit(_: WindowManager) -> bool:
        """if self.exit() == True: break"""

        return True

    def alert(self, detail: Any) -> None:
        """Show modal dialog displaying `detail`"""

        window: Window

        window = cast(
            Window,
            (
                Window(width=50, resizable=False, modal=True)
                + "[wm-title]Alert!"
                + ""
                + f"[wm-section]Detail[/]: {str(detail)}"
                + ""
                + ["Dismiss", lambda *_: window.close()]
            ).center(),
        )

        self.add(window)

    def debug(self) -> str:
        return f"WindowManager(Window() * {len(self._windows)})"


class DebugWindow(Window):
    """Window with debug capabilities"""

    def __init__(self, destroyer: Optional[MouseCallback] = None, **attrs: Any) -> None:
        """Initialize object"""

        # Set default title argument
        if "title" not in attrs:
            attrs["title"] = " debug "

        super().__init__(**attrs)
        self.min_width = 25
        self.forced_width = 50

        self._add_widget(Label("[210 bold]Debug"))
        self._add_widget(Label(""))

        if destroyer is None:
            destroyer = lambda _, widget: (
                widget.manager.close(widget) if widget.manager is not None else None
            )

        self.add_button("x").onclick = destroyer
        self.add_button("o").onclick = lambda _, window: window.toggle_fullscreen()

        self._add_widget(
            Button(
                "[157 bold]Align left",
                lambda *_: self.change_align(Widget.PARENT_LEFT),
            )
        )

        self._add_widget(
            Button(
                "[157 bold]Align center",
                lambda *_: self.change_align(Widget.PARENT_CENTER),
            )
        )

        self._add_widget(
            Button(
                "[157 bold]Align right",
                lambda *_: self.change_align(Widget.PARENT_RIGHT),
            )
        )

        self._add_widget(Label())

        self._add_widget(
            Button(
                "[157 bold]New window",
                lambda _, listview: listview.parent.manager.add(DebugWindow()),
            )
        )

        self._add_widget(
            Button(
                "[157 bold]New modal window",
                lambda _, listview: listview.parent.manager.add(
                    DebugWindow(modal=True)
                ),
            )
        )

        self._add_widget(
            Button(
                "[157 bold]New static window",
                lambda _, listview: listview.parent.manager.add(
                    DebugWindow(static=True)
                ),
            )
        )

        width, height = screen_size()
        self.pos = randint(0, width - self.width), randint(0, height - self.height - 2)

    def change_width(self, amount: int) -> None:
        """Increase/decrease widget width"""

        if self.width + amount > screen_width():
            return

        pos = list(self.pos)
        if self.forced_width is None:
            self.forced_width = self.width

        self.forced_width += amount
        self.width = self.forced_width

        self.pos = (pos[0], pos[1])


class MouseDebugger(Window):
    """Window to show mouse status"""

    def __init__(self, **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(title=" mouse ", **attrs)
        self.min_width = 25
        self.width = 25
        self.is_force_focus = True

        self._add_widget(Label("[wm-title]Mouse Information" ""))

        self._label_pos = Label(parent_align=0, padding=2)
        self._label_action = Label(parent_align=0, padding=2)
        self._label_target = Label(parent_align=0, padding=2)

        self._add_widget(Label("[wm-section]Position", parent_align=0))
        self._add_widget(self._label_pos)
        self._add_widget(Label("[wm-section]Action", parent_align=0))
        self._add_widget(self._label_action)

    def notify(self, event: Any) -> bool:
        """Receive event notification"""

        assert len(event) == 2
        action, pos = event

        # target = self.manager.focused.get_target(pos)

        self._label_pos.value = f"({pos[0]}, {pos[1]})"
        self._label_action.value = str(action)

        return False


class WindowDebugger(Window):
    """Window to show information on other windows"""

    def __init__(self, **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(title=" window ", **attrs)
        self.min_width = 25
        self.width = 25
        self.is_force_focus = True
        self.is_resizable = False

        self._add_widget(Label("[wm-title]Window information"))

        self._watching: dict[str, Callable[[Window], str]] = {
            "Title": lambda window: window.title,
            "Static": lambda window: str(window.is_static),
            "Modal": lambda window: str(window.is_modal),
            "Focus Override": lambda window: str(window.is_force_focus),
            "Position": lambda window: str(window.pos),
            "Size": lambda window: str((window.width, window.height)),
        }

    def get_lines(self) -> list[str]:
        """Update labels & get_lines"""

        self._widgets = [self._widgets[0]]

        if self.manager is not None:
            window = self.manager.focused
            if window is None:
                return super().get_lines()

            for label, method in self._watching.items():
                self._widgets.append(
                    Label("[wm-section]" + label, parent_align=Widget.PARENT_LEFT)
                )
                self._widgets.append(
                    Label(method(window), padding=2, parent_align=Widget.PARENT_LEFT)
                )

        return super().get_lines()


def test() -> None:
    """Run test program"""

    boxes.DOUBLE_TOP.set_chars_of(Window)
    Window.set_char("button", ["/", "\\"])

    def manager_exit(self: WindowManager) -> bool:
        """Ask for confirmation"""

        exit_dialog = (
            Window(modal=True)
            + Label("[wm-title]Really quit?")
            + Button("[157]Yes", lambda _, __: sys.exit(0))
            + Button("[157]No", lambda _, btn: btn.parent.manager.close(btn.parent))
        )

        assert isinstance(exit_dialog, Window)

        exit_dialog.center()

        self.add(exit_dialog)
        self.focus_window(exit_dialog)
        return False

    manager = WindowManager()
    setattr(manager, "exit", manager_exit)

    mouse_debugger = MouseDebugger()
    manager.set_mouse_listener(mouse_debugger)
    window_debugger = WindowDebugger()

    manager.add(mouse_debugger)
    manager.add(window_debugger)

    width, _ = screen_size()
    offset = 1
    for window in [mouse_debugger, window_debugger]:
        window.pos = (width - window.width + 1, offset)
        offset += window.height
        window.is_static = True

    root_window = DebugWindow(
        title=" root ",
        destroyer=lambda _, widget: widget.manager.exit(widget.manager)
        if widget.manager is not None
        else None,
    )

    manager.add(root_window)
    manager.run()


if __name__ == "__main__":
    test()
