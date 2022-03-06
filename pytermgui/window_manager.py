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
from typing import Optional, Any

# https://github.com/python/mypy/issues/4930
from .widgets.layouts import Container

from .widgets import (
    MarkupFormatter,
    Widget,
    boxes,
)

from .input import getch
from .parser import markup
from .animations import animator
from .helpers import strip_ansi, real_length
from .enums import CenteringPolicy, SizePolicy, Overflow
from .context_managers import alt_buffer, mouse_handler, MouseTranslator, cursor_at
from .ansi_interface import (
    terminal,
    background,
    MouseEvent,
    move_cursor,
    MouseAction,
)


__all__ = ["Window", "WindowManager"]


class Edge(Enum):
    """Enum for window edges."""

    LEFT = _auto()
    TOP = _auto()
    RIGHT = _auto()
    BOTTOM = _auto()


class Window(Container):
    """A class representing a window.

    Windows are essentially fancy `pytermgui.widgets.Container`-s. They build on top of them
    to store and display various widgets, while allowing some custom functionality.
    """

    is_bindable = True
    overflow = Overflow.HIDE

    allow_fullscreen = False
    """When a window is allowed fullscreen its manager will try to set it so before each frame."""

    title = ""
    """Title shown in left-top corner."""

    is_static = False
    """Static windows cannot be moved using the mouse."""

    is_modal = False
    """Modal windows stay on top of every other window and block interactions with other windows."""

    is_noblur = False
    """No-blur windows will always appear to stay in focus, even if they functionally don't."""

    is_noresize = False
    """No-resize windows cannot be resized using the mouse."""

    is_dirty = False
    """Control whether the parent manager needs to print this Window."""

    min_width: int | None = None
    """Minimum width of the window.

    If set to none, _auto_min_width will be calculated based on the maximum width of inner widgets.
    This is accurate enough for general use, but tends to lean to the safer side, i.e. it often
    overshoots the 'real' minimum width possible.

    If you find this to be the case, **AND** you can ensure that your window will not break, you
    may set this value manually."""

    styles = {**Container.styles, **{"title": MarkupFormatter("[wm-title]{item}")}}
    chars = Container.chars.copy()

    def __init__(self, *widgets: Any, **attrs: Any) -> None:
        """Initializes object.

        Args:
            widgets: Widgets to add to this window after initilization.
            attrs: Attributes that are passed to the constructor.
        """

        self._auto_min_width = 0

        super().__init__(*widgets, **attrs)

        self.has_focus: bool = False
        self.manager: Optional[WindowManager] = None

        # -------------------------  position ----- width x height
        self._restore_data: tuple[tuple[int, int], tuple[int, int]] | None = None

        if self.title != "":
            self.set_title(self.title)

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """Returns the tuple of positions that define this window.

        Returns:
            A tuple of integers, in the order (left, top, right, bottom).
        """

        left, top = self.pos
        return (left, top, left + self.width, top + self.height)

    @rect.setter
    def rect(self, new: tuple[int, int, int, int]) -> None:
        """Sets new position, width and height of this window.

        This method also checks for the minimum width this window can be, and
        if the new width doesn't comply with that setting the changes are thrown
        away.

        Args:
            new: A tuple of integers in the order (left, top, right, bottom).
        """

        left, top, right, bottom = new
        minimum = self.min_width or self._auto_min_width

        if right - left < minimum:
            return

        # Update size policy to fill to resize inner objects properly
        self.size_policy = SizePolicy.FILL
        self.pos = (left, top)
        self.width = right - left
        self.height = bottom - top
        # Restore original size policy
        self.size_policy = SizePolicy.STATIC

    def __iadd__(self, other: object) -> Window:
        """Calls self._add_widget(other) and returns self."""

        self._add_widget(other)
        return self

    def __add__(self, other: object) -> Window:
        """Calls self._add_widget(other) and returns self."""

        self._add_widget(other)
        return self

    def _add_widget(self, other: object, run_get_lines: bool = True) -> Widget:
        """Adds a widget to the window.

        Args:
            other: The widget-like to add.
            run_get_lines: Whether self.get_lines should be ran after adding.
        """

        added = super()._add_widget(other, run_get_lines)

        if self.min_width is None and len(self._widgets) > 0:
            self._auto_min_width = max(widget.width for widget in self._widgets)
            self._auto_min_width += self.sidelength

        self.height += added.height

        return added

    def nullify_cache(self) -> None:
        """Nullifies manager's cached blur state."""

        if self.manager is not None:
            self.manager.nullify_cache(self)

    def contains(self, pos: tuple[int, int]) -> bool:
        """Determines whether widget contains `pos`.

        This method uses window.rect to get the positions.

        Args:
            pos: Position to compare.

        Returns:
            Boolean describing whether the position is inside
              this widget.
        """

        left, top, right, bottom = self.rect

        return left <= pos[0] < right and top <= pos[1] < bottom

    def set_title(self, title: str, position: int = 0, pad: bool = True) -> None:
        """Sets the window's title.

        Args:
            title: The string to set as the window title.
            position: An integer indexing into ["left", "top", "right", "bottom"],
                determining where the title is applied.
            pad: Whether there should be an extra space before and after the given title.
                defaults to True.
        """

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
        """Sets window to fullscreen.

        Args:
            value: Whether fullscreen should be set or unset.

        Returns:
            The same window.
        """

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
    """A class representing a WindowManager."""

    is_bindable = True

    framerate = 60
    """Target framerate for rendering. Higher number means more resource usage."""

    focusing_actions: list[MouseAction] = [
        MouseAction.LEFT_CLICK,
        MouseAction.LEFT_DRAG,
        MouseAction.RIGHT_CLICK,
        MouseAction.RIGHT_DRAG,
    ]
    """A list of MouseAction-s that, when executed over a non-focused window will focus it."""

    def __init__(self, **attrs: Any) -> None:
        """Initialize object."""

        super().__init__(**attrs)

        self._is_paused: bool = False
        self._is_running: bool = True
        self._should_print: bool = False
        self._windows: list[Window] = []
        self._drag_target: tuple[Widget, Edge | None] | None = None  # type: ignore
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
        """Accurately sleeps some duration.

        Args:
            duration: The amount to sleep.
        """

        # TODO: Implement a better sleep function

        return time.sleep(duration)

    @property
    def should_print(self) -> bool:
        """Returns whether the `WindowManager` has dirty elements.

        An element being "dirty" means it has changes not yet shown. Windows
        can set themselves to be dirty using the `Window.is_dirty` flag."""

        return (
            animator.is_active
            or self._should_print
            or any(window.is_dirty for window in self._windows)
        )

    def __enter__(self) -> WindowManager:
        """Starts context manager."""

        return self

    def __exit__(self, _: Any, exception: Exception, __: Any) -> bool:
        """Ends context manager."""

        if exception is not None:
            self.stop()
            raise exception

        return True

    def _start_display_thread(self) -> None:
        """The loop that handles all displaying

        This is run as a thread, with `process_input` occupying
        the main line."""

        def _loop() -> None:
            """Body of thread"""

            last_frame = time.perf_counter()
            prev_framerate = self.framerate

            fps_start_time = last_frame
            frametime = 1 / self.framerate
            framecount = 0

            while self._is_running:
                if prev_framerate != self.framerate:
                    frametime = 1 / self.framerate
                    prev_framerate = self.framerate

                if self._is_paused or not self.should_print:
                    self._sleep(frametime)
                    framecount += 1
                    continue

                elapsed = time.perf_counter() - last_frame
                if elapsed < frametime:
                    self._sleep(frametime - elapsed)
                    framecount += 1
                    continue

                animator.step()
                self.print()

                last_frame = time.perf_counter()

                if last_frame - fps_start_time >= 1:
                    self.fps = framecount
                    fps_start_time = last_frame
                    framecount = 0

                framecount += 1

        Thread(name="WM_DisplayLoop", target=_loop).start()

    def nullify_cache(self, window: Window) -> None:
        """Nullifies a window's cache.

        All contained windows use caching to save on performance. Cache
        gets automatically nullified if a window changes while it is
        focused, but not if a window changes while unfocused.

        To get the correct behavior in that instance, use `Window.nullify_cache`,
        which calls this method.

        Args:
            window: The window whos cache we will nullify.
        """

        if id(window) in self._window_cache:
            del self._window_cache[id(window)]

    def execute_binding(self, key: Any) -> bool:
        """Execute bindings, including mouse ones.

        Args:
            key: The binding to execute, if found.

        Returns:
            Boolean describing success.
        """

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
        """Process a keypress.

        Args:
            key: The key to handle.

        Returns:
            A boolean describing success.
        """

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
        """Processes (potential) mouse input.

        Args:
            key: Input to handle.
        """

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
            # Ignore null-events
            if event is None:
                continue

            self._should_print = True

            for window in self._windows:
                contains_pos = window.contains(event.position)
                is_target = (
                    self._drag_target is not None and self._drag_target[0] is window
                )

                if not contains_pos and not is_target:
                    if window.is_modal:
                        break

                    continue

                if event.action in self.focusing_actions:
                    self.focus(window)

                if window.handle_mouse(event):
                    break

                if event.action in handlers and handlers[event.action](
                    event.position, window
                ):
                    break

                if not contains_pos and not window.is_modal:
                    continue

                self.execute_binding(tuple(event))

                # Break on modal window
                if window.is_modal or contains_pos:
                    break

            # Unset drag_target if no windows received the input
            else:
                self._drag_target = None

    def focus(self, window: Window) -> None:
        """Sets a window to be focused.

        Args:
            window: The window to focus.
        """

        if self.focused is not None:
            self.focused.handle_mouse(MouseEvent(MouseAction.RELEASE, (0, 0)))

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
        """Adds a window to this manager.

        Args:
            window: The window to add.

        Returns:
            self.
        """

        original_height = window.height

        def _on_step(window: Widget) -> None:
            """Sets window's height on step, centers it."""

            assert isinstance(window, Window)
            window.height = original_height
            if window.centered_axis is not None:
                window.center()

        self._windows.insert(0, window)
        self._should_print = True
        window.manager = self

        # New windows take focus-precedence over already
        # existing ones, even if they are modal.
        self.focus(window)

        animator.animate(
            window,
            "width",
            startpoint=int(window.width * 0.7),
            endpoint=window.width,
            duration=150,
            step_callback=_on_step,
        )
        return self

    def close(self, window: Window) -> None:
        """Closes a window.

        Args:
            window: The window to close.
        """

        old_overflow = window.overflow
        old_height = window.height

        def _finish(window: Widget) -> None:
            """Finish closing the window after animation."""

            assert isinstance(window, Window)
            self._windows.remove(window)
            if window.has_focus and len(self._windows) > 0:
                self.focus(self._windows[0])

            window.overflow = old_overflow
            window.height = old_height

            # NOTE: This is supposed to work using `_should_print`, but it doesn't.
            # Force print
            self.print()

        window.overflow = Overflow.HIDE
        animator.animate(
            window,
            "height",
            endpoint=0,
            duration=150,
            finish_callback=_finish,
        )

    def on_resize(self, size: tuple[int, int]) -> None:
        """Correctly updates window positions & prints when terminal gets resized.

        Args:
            size: The new terminal size.
        """

        width, height = size

        for window in self._windows:
            newx = max(0, min(window.pos[0], width - window.width))
            newy = max(0, min(window.pos[1], height - window.height + 1))

            window.pos = (newx, newy)

        self._should_print = True

    def _click(self, pos: tuple[int, int], window: Window) -> bool:
        """Process clicking a window."""

        left, top, right, bottom = window.rect

        if pos[1] == top and left <= pos[0] < right:
            self._drag_target = (window, Edge.TOP)

        elif pos[1] == bottom - 1 and left <= pos[0] < right:
            self._drag_target = (window, Edge.BOTTOM)

        elif pos[0] == left and top <= pos[1] < bottom:
            self._drag_target = (window, Edge.LEFT)

        elif pos[0] == right - 1 and top <= pos[1] < bottom:
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

        left, top, right, bottom = window.rect
        if not window.is_static and edge is Edge.TOP:
            window.pos = (
                _clamp_pos(0),
                _clamp_pos(1),
            )

            handled = True

        # TODO: Why are all these arbitrary offsets needed?
        elif not window.is_noresize:
            if edge is Edge.RIGHT:
                window.rect = (left, top, pos[0] + 1, bottom)
                handled = True

            elif edge is Edge.LEFT:
                window.rect = (pos[0], top, right, bottom)
                handled = True

            elif edge is Edge.BOTTOM:
                window.rect = (left, top, right, pos[1] + 1)
                handled = True

        # Wipe window from cache
        if id(window) in self._window_cache:
            del self._window_cache[id(window)]

        return handled

    def _release(self, _: tuple[int, int], __: Window) -> bool:
        """Process release of key"""

        self._drag_target = None

        # This return False so Window can handle the mouse action as well,
        # as not much is done in this callback.
        return False

    def process_input(self) -> None:
        """Processes incoming input."""

        while self._is_running:
            key = getch(interrupts=False)

            if key == chr(3):
                self.stop()
                break

            if self.handle_key(key):
                self._should_print = True
                continue

            self.process_mouse(key)

    def stop(self) -> None:
        """Stops the main loop."""

        self._is_running = False

    def pause(self) -> None:
        """Pauses the main loop."""

        self._is_paused = True

    def unpause(self) -> None:
        """Pauses the main loop."""

        self._is_paused = False

    def exit(self) -> None:
        """Exits the program."""

        self.stop()
        sys.exit()

    def run(self, mouse_events: list[str] | None = None) -> None:
        """Runs the main loop.

        Args:
            mouse_events: A list of mouse event types to listen to. See
                `pytermgui.ansi_interface.report_mouse` for more information.
                Defaults to `["press_hold", "hover"]`.
        """

        if mouse_events is None:
            mouse_events = ["press_hold", "hover"]

        with alt_buffer(cursor=False, echo=False):
            with mouse_handler(mouse_events, "decimal_xterm") as translate:
                self.mouse_translator = translate
                self._start_display_thread()

                self.process_input()

    def print(self) -> None:
        """Prints all windows."""

        def _get_lines(window: Window) -> list[str]:
            """Get cached or live lines from a Window"""

            # This optimization is really important for
            # a lot of windows being rendered.
            if id(window) in self._window_cache:
                return self._window_cache[id(window)]

            lines: list[str] = []
            for line in window.get_lines():
                lines.append(markup.parse("[239]" + strip_ansi(line)))

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
                window.print()
                continue

            lines = _get_lines(window)
            for i, line in enumerate(lines):
                move_cursor((window.pos[0], window.pos[1] + i))
                sys.stdout.write(line)

        sys.stdout.flush()
        self._should_print = False

    def show_targets(self) -> None:
        """Shows all windows' positions."""

        def _show_positions(widget, color_base: int = 60) -> None:
            """Show positions of widget."""

            if isinstance(widget, Container):
                for i, subwidget in enumerate(widget):
                    _show_positions(subwidget, color_base + i)

                return

            if not widget.is_selectable:
                return

            with cursor_at(widget.pos) as pprint:
                debug = widget.debug()
                buff = background(" ", color_base, reset_color=False)

                for i in range(min(widget.width, real_length(debug)) - 1):
                    buff += debug[i]

                pprint(buff)

        self.pause()
        for widget in self._windows:
            _show_positions(widget)

        getch()
        self.unpause()

        self._should_print = True

    def alert(self, *content: Any) -> None:
        """Create a modal window with content.

        Args:
            *content: The content to add to the new window.
        """

        window = Window("[wm-title]Alert!", is_modal=True, width=50)
        for item in content:
            window += item

        window += ""
        window += ["Dismiss", lambda *_: window.close()]
        window.select(0)

        self.add(window.center())
        self.focus(window)
