"""
Description
-----------

A full implementation of a WindowManager for the terminal, building on top
of the Widget system.

It runs with no external dependencies, and has full mouse support. It is the
simplest way to use pytermgui in your applications, as it handles all input
and output in a nice and optimized manner.

It runs in two threads:
- Main thread (blocking): `WindowManager.process_input`

- WM_DisplayLoop (non-blocking): `WindowManager._start_display_thread`

Usage example
-------------

```python3
import pytermgui as ptg

with ptg.WindowManager() as manager:
    manager.add(
        ptg.Window()
        + "[wm-title]Hello world!"
        + ""
        + {"[wm-section]Key1": ["value1", lambda *_: manager.alert("Value1")]}
        + {"[wm-section]Key2": ["value2", lambda *_: manager.alert("Value2")]}
        + ""
        + ptg.InputField(prompt="Your input:")
        + ""
        + ["Submit!", lambda *_: manager.alert("Form submitted!")]
    )

    manager.run()
```

<img src=https://github.com/bczsalba/pytermgui/blob/master/assets/docs/wm_demo.gif?raw=true
style="max-width: 100%">
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
from typing import Optional, Any, cast

# https://github.com/python/mypy/issues/4930
from .widgets.base import Container

from .widgets import (
    MarkupFormatter,
    Widget,
    boxes,
)

from .input import getch
from .parser import markup
from .helpers import strip_ansi
from .exceptions import LineLengthError
from .enums import CenteringPolicy, SizePolicy
from .context_managers import alt_buffer, mouse_handler, MouseTranslator
from .ansi_interface import (
    terminal,
    MouseEvent,
    move_cursor,
    MouseAction,
)


__all__ = ["Window", "WindowManager"]


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
        self.bottom = self.end[1] + 3

        self.values = self.left, self.top, self.right, self.bottom

    @classmethod
    def from_widget(cls, widget: Widget) -> Rect:
        """Create a Rect from a widget"""

        start = widget.pos
        end = start[0] + widget.width, start[1] + widget.height
        return cls(start, end)

    @classmethod
    def from_tuple(cls, tpl: tuple[int, int, int, int]) -> Rect:
        """Create a Rect from a tuple of points"""

        startx, starty, endx, endy = tpl
        return cls((startx, starty), (endx, endy))

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
        """Determine if position is contained within this area"""

        return self.left <= pos[0] <= self.right and self.top <= pos[1] <= self.bottom

    def show(self) -> None:
        """Draw rect on screen"""

        root = Container(width=self.right - self.left)
        root += self.debug()
        root.forced_width = self.right - self.left
        root.forced_height = self.top - self.bottom
        root.pos = self.start

        root.print()

    def debug(self) -> str:
        """Show identifiable debug information"""

        return str(Widget.debug(cast(Widget, self)))


class Window(Container):
    """A class representing a window

    Windows are essentially fancy `pytermgui.widgets.Container`-s. They build on top of them
    to store and display various widgets, while allowing some custom functionality.
    """

    is_bindable = True
    size_policy = SizePolicy.STATIC

    allow_fullscreen = False
    """When a window is allowed fullscreen its manager will try to set it so before each frame"""

    title = ""
    """Title shown in left-top corner"""

    is_static = False
    """Static windows cannot be moved using the mouse"""

    is_modal = False
    """Modal windows stay on top of every other window and block interactions with other windows"""

    is_noblur = False
    """No-blur windows will always appear to stay in focus, even if they functionally don't"""

    is_noresize = False
    """No-resize windows cannot be resized using the mouse"""

    styles = {**Container.styles, **{"title": MarkupFormatter("[wm-title]{item}")}}

    def __init__(self, *widgets: Any, **attrs: Any) -> None:
        """Initialize object"""

        self.is_dirty: bool = False

        super().__init__(*widgets, **attrs)

        self.has_focus: bool = False
        self.manager: Optional[WindowManager] = None

        # -------------------------  position ----- width x height
        self._restore_data: tuple[tuple[int, int], tuple[int, int]] | None = None

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

        left, top, right, _ = new.values
        self.pos = (left, top)
        self.width = right - left

    def __iadd__(self, other: object) -> Window:
        """Call self._add_widget(other) and return self"""

        self._add_widget(other)
        return self

    def set_title(self, title: str, position: int = 0, pad: bool = True) -> None:
        """Set window title"""

        self.title = title

        title = "[wm-title]" + title
        if pad:
            title = " " + title + " "

        corners = self._get_char("corner")
        assert isinstance(corners, list)

        if position % 2 == 0:
            corners[position] += title

        else:
            current = corners[position]
            corners[position] = title + current

        self.set_char("corner", corners)

    def set_fullscreen(self, value: bool = True) -> Window:
        """Set window to fullscreen"""

        if value:
            self._restore_data = self.pos, (self.width, self.height)

            self.pos = terminal.origin
            self.allow_fullscreen = True
            self.size_policy = SizePolicy.FILL

        else:
            assert self._restore_data is not None
            self.pos, (self.width, self.height) = self._restore_data

            self._restore_data = None
            self.allow_fullscreen = False
            self.size_policy = SizePolicy.STATIC

        return self

    def center(
        self, where: CenteringPolicy | None = None, store: bool = True
    ) -> Window:
        """Center window"""

        super().center(where, store)
        return self

    def close(self) -> None:
        """Instruct window manager to close object"""

        assert self.manager is not None
        self.manager.close(self)

    def print(self) -> None:
        """Print without flushing"""

        for i, line in enumerate(self.get_lines()):
            sys.stdout.write(f"\033[{self.pos[1] + i};{self.pos[0]}H" + line)

        self._has_printed = True


class WindowManager(Container):
    """A class representing a WindowManager"""

    is_bindable = True

    framerate = 120
    """Target framerate for rendering. Higher number means more resource usage."""

    def __init__(self, **attrs: Any) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self._is_paused: bool = False
        self._is_running: bool = True
        self._should_print: bool = False
        self._windows: list[Window] = []
        self._drag_target: tuple[Widget, Edge] | None = None  # type: ignore
        self._drag_offsets: tuple[int, int] = (1, 1)

        self._window_cache: dict[int, list[str]] = {}

        self.fps: int | None = None
        self.focused: Window | None = None
        self.mouse_translator: MouseTranslator | None = None

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

    @property
    def should_print(self) -> bool:
        """Whether the `WindowManager` has dirty elements

        An element being "dirty" means it has changes not yet shown. Windows
        can set themselves to be dirty using the `Window.is_dirty` flag."""

        return self._should_print or any(window.is_dirty for window in self._windows)

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

        This is run as a thread, with `process_input` occupying
        the main line."""

        def _loop() -> None:
            """Body of thread"""

            last_frame = time.perf_counter()
            frametime = 1 / self.framerate

            fps_start_time = time.perf_counter()
            framecount = 0

            while self._is_running:
                if self._is_paused or not self.should_print:
                    self._sleep(frametime)
                    continue

                # Don't print before frametime elapsed
                # TODO: This is imprecise, framerate is not followed well
                if time.perf_counter() - last_frame < frametime:
                    # time.sleep(sleeptime)
                    continue

                self.print()

                last_frame = time.perf_counter()

                if last_frame - fps_start_time >= 1:
                    self.fps = framecount
                    fps_start_time = last_frame
                    framecount = 0

                framecount += 1

        Thread(name="WM_DisplayLoop", target=_loop).start()

    def execute_binding(self, key: Any) -> bool:
        """Execute bindings, including mouse ones"""

        if not isinstance(key, str):
            return super().execute_binding(key)

        # Execute universal mouse binding
        if self.mouse_translator is None:
            events = None
        else:
            events = self.mouse_translator(key)

        if events is not None:
            handled = False
            for event in events:
                if not isinstance(event, MouseEvent):
                    continue

                bound = self._bindings.get(MouseEvent)
                if bound is None:
                    continue

                method, _ = bound
                handled = method(self, event)

            if handled:
                return True

        return super().execute_binding(key)

    def handle_key(self, key: str) -> bool:
        """Process a keypress"""

        # Apply WindowManager bindings
        if self.execute_binding(key):
            return True

        # Apply focused window binding, or send to InputField
        if self.focused is not None:
            if self.focused.execute_binding(key):
                return True

            if self.focused.handle_key(key):
                return True

        return False

    def process_mouse(self, key: str) -> None:
        """Process (potential) mouse input"""

        def _get_target() -> Window | None:
            """Get current drag target window"""

            if self._drag_target is None:
                return None

            win = self._drag_target[0]
            assert isinstance(win, Window) or win is None
            return win

        handlers = {
            MouseAction.LEFT_CLICK: self._click,
            MouseAction.LEFT_DRAG: self._drag,
            MouseAction.RELEASE: self._release,
        }

        translate = self.mouse_translator
        event_list = None if translate is None else translate(key)

        if event_list is None:
            return

        for event in event_list:
            target_window = _get_target()

            # Ignore null-events
            if event is None:
                continue

            # Mypy sees `event` as a tuple[MouseAction, tuple[int, int]] for some reason.
            action, pos = cast(MouseEvent, event)

            for window in self._windows:
                if window is target_window or window.rect.contains(pos):
                    if action is not MouseAction.HOVER and not window.has_focus:
                        self.focus(window)

                    if (
                        not window.handle_mouse(cast(MouseEvent, event))
                        and action in handlers
                    ):
                        handlers[action](pos, window)

                    self._should_print = True

                    self.execute_binding((action, pos))
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

        # Don't crash if window was removed
        if not window in self._windows:
            return

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

        if window.has_focus and len(self._windows) > 0:
            self.focus(self._windows[0])

    def on_resize(self, size: tuple[int, int]) -> None:
        """Correctly update window positions & print when terminal gets resized"""

        width, height = size

        for window in self._windows:
            newx = max(0, min(window.pos[0], width - window.width))
            newy = max(0, min(window.pos[1], height - window.height + 1))

            window.pos = (newx, newy)

        self._should_print = True

    def _click(self, pos: tuple[int, int], window: Window) -> bool:
        """Process clicking a window"""

        left, top, right, bottom = window.rect.values

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

    def _drag(self, pos: tuple[int, int], window: Window) -> bool:
        """Process dragging a window"""

        def _clamp_pos(index: int) -> int:
            """Clamp a value using index to address x/y & width/height"""

            offset = self._drag_offsets[index]

            # TODO: This -2 is a very magical number. Not good.
            maximum = terminal.size[index] - ((window.width, window.height)[index] - 2)

            start_margin_index = abs(index - 1)
            return max(
                index + terminal.margins[start_margin_index],
                min(
                    pos[index] - offset,
                    maximum - terminal.margins[start_margin_index + 2],
                ),
            )

        if self._drag_target is None:
            return False

        target_window, edge = self._drag_target
        handled = False

        if window is not target_window:
            return False

        left, top, right, bottom = window.rect.values
        if not window.is_static and edge is Edge.TOP:
            window.pos = (
                _clamp_pos(0),
                _clamp_pos(1),
            )

            handled = True

        elif not window.is_noresize:
            if edge is Edge.RIGHT:
                window.rect = Rect.from_tuple((left, top, pos[0] + 1, bottom))
                handled = True

            elif edge is Edge.LEFT:
                window.rect = Rect.from_tuple(
                    (pos[0], top, right + left - pos[0], bottom)
                )
                handled = True

        try:
            window.get_lines()
        except LineLengthError:
            window.rect = Rect.from_tuple((left, top, right, bottom))

        # Wipe window from cache
        if id(window) in self._window_cache:
            del self._window_cache[id(window)]

        return handled

    def _release(self, _: tuple[int, int], __: Window) -> bool:
        """Process release of key"""

        self._drag_target = None
        return True

    def process_input(self) -> None:
        """Process incoming input"""

        while self._is_running:
            key = getch()

            if self.handle_key(key):
                self._should_print = True
                continue

            self.process_mouse(key)

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
        """Run main loop"""

        with alt_buffer(cursor=False, echo=False):
            with mouse_handler(["press_hold", "hover"], "decimal_xterm") as translate:
                self.mouse_translator = translate
                self._start_display_thread()

                self.process_input()

    def print(self) -> None:
        """Print all windows"""

        def _get_lines(window: Window) -> list[str]:
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
            # TODO: Why are these offsets needed?
            if window.allow_fullscreen:
                window.pos = terminal.origin
                window.width = terminal.width + 1
                window.height = terminal.height + 3

            if window.has_focus or window.is_noblur:
                try:
                    window.print()
                except LineLengthError:
                    pass
                continue

            lines = _get_lines(window)
            for i, line in enumerate(lines):
                move_cursor((window.pos[0], window.pos[1] + i))
                sys.stdout.write(line)

        sys.stdout.flush()
        self._should_print = False

    def show_targets(self, color: int | None = None) -> None:
        """Show all windows' targets"""

        self.pause()
        for window in self._windows:
            window.show_targets(color)

        getch()
        self.unpause()

        self._should_print = True

    def alert(self, *content: Any) -> None:
        """Create a modal window with content"""

        window = Window("[wm-title]Alert!", is_modal=True, width=50)
        for item in content:
            window += item

        window += ""
        window += ["Dismiss", lambda *_: window.close()]
        window.select(0)

        self.add(window.center())
        self.focus(window)
