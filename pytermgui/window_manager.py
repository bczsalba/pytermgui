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
import time
import signal
from threading import Thread
from enum import Enum, auto as _auto
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

# https://github.com/python/mypy/issues/4930
from .widgets.base import Container

from .widgets import (
    MarkupFormatter,
    InputField,
    Widget,
    boxes,
)

from .parser import markup
from .input import getch, keys
from .exceptions import LineLengthError
from .helpers import strip_ansi
from .ansi_interface import terminal, MouseAction, move_cursor
from .context_managers import alt_buffer, mouse_handler, MouseEvent


# __all__ = ["Window", "WindowManager", "DebugWindow", "MouseDebugger", "WindowDebugger"]
__all__ = ["WindowManager", "Window"]


class Edge(Enum):
    """Enum for window edges"""

    LEFT = _auto()
    TOP = _auto()
    RIGHT = _auto()
    BOTTOM = _auto()


@dataclass
class Rect:
    """A class representing a screen region"""

    start: tuple[int, int]
    end: tuple[int, int]

    left: int = field(init=False)
    right: int = field(init=False)
    top: int = field(init=False)
    bottom: int = field(init=False)

    def __post_init__(self) -> None:
        """Set up extra instance attributes"""

        self.left = self.start[0]
        self.right = self.end[0] - 1
        self.top = self.start[1]
        self.bottom = self.end[1] - 1

    def __iter__(self) -> None:
        """Iterate through data"""

        for item in (self.left, self.top, self.right, self.bottom):
            yield item

    @classmethod
    def from_widget(cls, widget: Widget) -> Rect:
        """Create a Rect from a widget"""

        start = widget.pos
        end = start[0] + widget.width, start[1] + widget.height
        return cls(start, end)

    @property
    def width(self) -> int:
        """Calculate width of rect"""

        return self.end[0] - self.start[0]

    @property
    def height(self) -> int:
        """Calculate height of rect"""

        return self.end[1] - self.start[1]

    def collides_with(self, other: Rect) -> bool:
        """Calculate collision with other Rect object"""

        return (
            self.left < other.right
            and self.right > other.left
            and self.top > other.bottom
            and self.bottom < other.top
        )

    def contains(self, pos: tuple[int, int]) -> bool:
        """Get if position is contained within this area"""

        return self.left <= pos[0] <= self.right and self.top <= pos[1] <= self.bottom

    def show(self) -> None:
        """Draw rect on screen"""

        root = Container(self.debug(), width=10)
        root.forced_width = self.right - self.left
        root.forced_height = self.top - self.bottom
        root.pos = self.start

        root.print()

    def debug(self) -> str:
        """Show identifiable debug information"""

        return Widget.debug(self)


class Window(Container):
    """A class representing a window

    A Window can have some attributes:
        modal: Only one in focus
        static: Non-draggable
        noresize: Non-resizable
        noblur: Never blurred, always in focus"""

    is_bindable = True

    title = ""
    is_static = False
    is_modal = False
    is_noblur = False
    is_noresize = False

    styles = {**Container.styles, **{"title": MarkupFormatter("[wm-title]{item}")}}

    def __init__(self, *widgets: Widget, **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(*widgets, **attrs)

        self.has_focus: bool = False
        self.manager: Optional[WindowManager] = None

        if self.title != "":
            self.set_title(self.title)

    @property
    def rect(self) -> Rect:
        """Return Rect representing this window"""

        # TODO: This probably shouldn't be done every time.
        return Rect.from_widget(self)

    @rect.setter
    def rect(self, new: tuple[int, int, int, int]) -> None:
        """Set new rect"""

        left, top, right, _ = new
        self.pos = (left, top)
        self.width = self.width = right - left

    def set_title(self, title: str, position: int = 0, pad: bool = True) -> None:
        """Set window title"""

        self.title = title

        title = "[wm-title]" + title
        if pad:
            title = " " + title + " "

        corners = self.get_char("corner")
        assert isinstance(corners, list)

        if position % 2 == 0:
            corners[position] += title

        else:
            current = corners[position]
            corners[position] = title + current

        self.set_char("corner", corners)

    def close(self) -> None:
        """Instruct window manager to close object"""

        self.manager.close(self)

    def print(self) -> None:
        """Print without flushing"""

        for i, line in enumerate(self.get_lines()):
            sys.stdout.write(f"\033[{self.pos[1] + i};{self.pos[0]}H" + line)


class WindowManager(Container):
    """A class representing a WindowManager"""

    is_bindable = True

    framerate = 300
    navigation_up: set[str] = {keys.UP, keys.CTRL_P, "k"}
    navigation_down: set[str] = {keys.DOWN, keys.CTRL_N, "j"}

    def __init__(self, **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self._is_paused: bool = False
        self._is_running: bool = True
        self._should_print: bool = False
        self._windows: list[Window] = []
        self._drag_target: Optional[tuple[Window, Edge]] = None
        self._drag_offsets: tuple[int, int] = (1, 1)
        self._mouse_translator: Optional[Callable[[str], MouseEvent]] = None

        self._window_cache: dict[str, list[str]] = {}

        self.focused: Optional[Window] = None

        # Handle some events
        terminal.subscribe(terminal.RESIZE, self.on_resize)
        signal.signal(signal.SIGINT, lambda *_: self.exit())

        # Set global styles
        markup.alias("wm-title", "210 bold")
        markup.alias("wm-section", "157")
        boxes.DOUBLE_TOP.set_chars_of(Window)

    @staticmethod
    def _sleep(duration: float) -> None:
        """Accurately sleep some duration"""

        # TODO: Implement a better sleep function

        return time.sleep(duration)

    def __enter__(self) -> WindowManager:
        """Start context manager"""

        return self

    def __exit__(self, _: Any, exception: Exception, __: Any) -> bool:
        """End context manager"""

        if exception is not None:
            raise exception

        self.stop()
        return True

    def _start_display_thread(self) -> None:
        """The loop that handles all displaying

        This is run as a thread, with `process_input()` occupying
        the main line."""

        def _loop() -> None:
            """Body of thread"""

            last_frame = time.perf_counter()
            frametime = 1 / self.framerate

            while self._is_running:
                if self._is_paused or not self._should_print:
                    self._sleep(frametime)
                    continue

                delta = time.perf_counter() - last_frame

                # Don't print before frametime elapsed
                if delta < frametime:
                    self._sleep(frametime - delta)
                    continue

                self.print()
                last_frame = time.perf_counter()

        Thread(name="WM_DisplayLoop", target=_loop).start()

    def _is_nav_key(self, key: str) -> bool:
        """Check if key is in any of the navigation sets"""

        return key in self.navigation_up | self.navigation_down

    def _handle_keypress(self, key: str) -> bool:
        """Process a keypress"""

        # Apply WindowManager bindings
        if self.execute_binding(key):
            return True

        # Apply focused window binding, or send to InputField
        if self.focused is not None:
            if self.focused.execute_binding(key):
                return True

            if isinstance(self.focused.selected, InputField):
                if self.focused.selected.send(key):
                    return True

        # Try handling key by window
        window = self.focused

        if window is not None:
            if self._is_nav_key(key) and window.selectables_length > 0:
                if window.selected_index is None:
                    window.selected_index = 0

                elif key in self.navigation_up:
                    window.selected_index -= 1

                elif key in self.navigation_down:
                    window.selected_index += 1

                window.select()
                return True

            if key == keys.ENTER and window.selected_index is not None:
                window.mouse_targets[window.selected_index].click(self)
                return True

        return False

    def _handle_mouse(self, key: str) -> None:
        """Process (potential) mouse input"""

        def _get_target() -> Window | None:
            """Get current drag target window"""

            if self._drag_target is None:
                return None

            return self._drag_target[0]

        handlers = {
            MouseAction.LEFT_DRAG: self.process_drag,
            MouseAction.RELEASE: self.process_release,
            MouseAction.LEFT_CLICK: self.process_click,
        }

        translate = self._mouse_translator
        event_list = None if translate is None else translate(key)

        if event_list is None:
            return

        for event in event_list:
            target_window = _get_target()

            # Ignore null-events
            if event is None:
                continue

            action, pos = event

            for window in self._windows:
                # Ignore unhandled actions
                if not action in handlers:
                    continue

                if window is target_window or window.rect.contains(pos):
                    if not window.has_focus:
                        self.focus(window)

                    self._should_print = handlers[action](pos, window)
                    break

                # Break on modal window
                if window.is_modal:
                    break

            # Unset drag_target if no windows received the input
            else:
                self._drag_target = None

    def focus(self, window: Window) -> None:
        """Set a window to be focused"""

        for other_window in self._windows:
            other_window.has_focus = False

        window.has_focus = True
        self._windows.remove(window)
        self._windows.insert(0, window)
        self.focused = window

    def add(self, window: Window) -> WindowManager:
        """Add a window to this manager"""

        self._windows.insert(0, window)
        self._should_print = True
        window.manager = self

        # New windows take focus-precedence over already
        # existing ones, even if they are modal.
        self.focus(window)

        return self

    def close(self, window: Window) -> None:
        """Close a window"""

        self._windows.remove(window)

    def on_resize(self, size: tuple[int, int]) -> None:
        """Correctly update window positions & print when terminal gets resized"""

        width, height = size

        for window in self._windows:
            newx = max(0, min(window.pos[0], width - window.width))
            newy = max(0, min(window.pos[1], height - window.height))

            window.pos = (newx, newy)

        self._should_print = True

    def process_click(self, pos: tuple[int, int], window: Window) -> bool:
        """Process clicking a window"""

        target = window.get_target(pos)
        if target is not None:
            window.select(window.mouse_targets.index(target))
            target.click(window.selected)
            return True

        left, top, right, bottom = window.rect

        if pos[1] == top and left <= pos[0] <= right:
            self._drag_target = (window, Edge.TOP)

        elif pos[1] == bottom and left <= pos[0] <= right:
            self._drag_target = (window, Edge.BOTTOM)

        elif pos[0] == left and top <= pos[1] <= bottom:
            self._drag_target = (window, Edge.LEFT)

        elif pos[0] == right and top <= pos[1] <= bottom:
            self._drag_target = (window, Edge.RIGHT)

        else:
            return False

        self._drag_offsets = (
            pos[0] - window.pos[0],
            pos[1] - window.pos[1],
        )

        return True

    def process_drag(self, pos: tuple[int, int], window: Window) -> bool:
        """Process dragging a window"""

        def _clamp_pos(index: int) -> int:
            """Clamp a value using index to address x/y & width/height"""

            offset = self._drag_offsets[index]
            maximum = terminal.size[index] - (window.width, window.height)[index]

            return max(index, min(pos[index] - offset, maximum))

        if self._drag_target is None:
            return False

        target_window, edge = self._drag_target

        if window is not target_window:
            return False

        left, top, right, bottom = window.rect
        if edge is Edge.TOP:
            window.pos = (
                _clamp_pos(0),
                _clamp_pos(1),
            )

        elif edge is Edge.RIGHT:
            window.rect = left, top, pos[0] + 1, bottom

        elif edge is Edge.LEFT:
            window.rect = pos[0], top, right + left - pos[0], bottom

        try:
            window.get_lines()
        except LineLengthError:
            window.rect = left, top, right, bottom

        if id(window) in self._window_cache:
            del self._window_cache[id(window)]

        return True

    def process_release(self, _: tuple[int, int], window: Window) -> bool:
        """Process release of key"""

        selected = self.focused
        while hasattr(selected, "selected"):
            selected = selected.selected

        if not isinstance(selected, InputField):
            window.selected_index = None

        self._drag_target = None
        return True

    def process_input(self) -> bool:
        """Process incoming input, set should_print"""

        while self._is_running:
            key = getch()

            if self._handle_keypress(key):
                self._should_print = True
                continue

            self._handle_mouse(key)

    def stop(self) -> None:
        """Stop main loop"""

        self._is_running = False

    def pause(self) -> None:
        """Pause main loop"""

        self._is_paused = True

    def unpause(self) -> None:
        """Pause main loop"""

        self._is_paused = False

    def exit(self) -> None:
        """Exit program"""

        self.stop()
        sys.exit()

    def run(self) -> None:
        """Run main WindowManager loop"""

        with alt_buffer(cursor=False, echo=False):
            with mouse_handler("press_hold", "decimal_urxvt") as translate:
                self._mouse_translator = translate
                self._start_display_thread()

                self.process_input()

    def print(self) -> None:
        """Print all windows"""

        def _get_lines(window) -> list[str]:
            """Get cached or live lines from a Window"""

            # This optimization is really important for
            # a lot of windows being rendered.
            if id(window) in self._window_cache:
                return self._window_cache[id(window)]

            lines = []
            for line in window.get_lines():
                lines.append(
                    markup.parse("[239]" + strip_ansi(line).replace("[", r"\["))
                )

            self._window_cache[id(window)] = lines
            return lines

        sys.stdout.write("\033[2J")
        for window in reversed(self._windows):
            if window.has_focus or window.is_noblur:
                try:
                    window.print()
                except LineLengthError:
                    continue
                continue

            lines = _get_lines(window)
            for i, line in enumerate(lines):
                move_cursor((window.pos[0], window.pos[1] + i))
                sys.stdout.write(line)

        sys.stdout.flush()
        self._should_print = False

    def show_targets(self, color: int = 210) -> None:
        """Show all windows' targets"""

        self.pause()
        for window in self._windows:
            window.show_targets(color)

        getch()
        self.unpause()

        self._should_print = True

    def alert(self, *content) -> None:
        """Create a modal window with content"""

        window = Window("[wm-title]Alert!", is_modal=True, width=50)
        for item in content:
            window += item

        window += ""
        window += ["Dismiss", lambda *_: window.close()]
        window.select(0)

        self.add(window.center())
        self.focus(window)
