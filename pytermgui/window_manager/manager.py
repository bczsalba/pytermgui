"""The WindowManager class, whos job it is to move, control and update windows,
while letting `Compositor` draw them."""

from __future__ import annotations

from enum import Enum, auto as _auto
from typing import Type, Any, Iterator

from ..input import getch
from ..enums import Overflow
from ..regex import real_length
from ..terminal import terminal
from ..colors import str_to_color
from ..widgets import Widget, Container
from ..widgets.base import BoundCallback
from ..ansi_interface import MouseAction, MouseEvent
from ..context_managers import alt_buffer, mouse_handler, MouseTranslator
from ..animations import animator, AttrAnimation, FloatAnimation, Animation

from .window import Window
from .layouts import Layout
from .compositor import Compositor


def _center_during_animation(animation: AttrAnimation) -> None:
    """Centers a window, when applicable, while animating."""

    window = animation.target
    assert isinstance(window, Window), window

    if window.centered_axis is not None:
        window.center()


class Edge(Enum):
    """Enum for window edges."""

    LEFT = _auto()
    TOP = _auto()
    RIGHT = _auto()
    BOTTOM = _auto()


class WindowManager(Widget):  # pylint: disable=too-many-instance-attributes
    """The manager of windows.

    This class can be used, or even subclassed in order to create full-screen applications,
    using the `pytermgui.window_manager.window.Window` class and the general Widget API.
    """

    is_bindable = True

    focusing_actions = (MouseAction.LEFT_CLICK, MouseAction.RIGHT_CLICK)
    """These mouse actions will focus the window they are acted upon."""

    def __init__(
        self,
        *,
        autorun: bool = True,
        layout_type: Type[Layout] = Layout,
        framerate: int = 60,
    ) -> None:
        """Initialize the manager."""

        super().__init__()

        self._is_running = False
        self._windows: list[Window] = []
        self._drag_offsets: tuple[int, int] = (0, 0)
        self._drag_target: tuple[Window, Edge] | None = None
        self._bindings: dict[str | Type[MouseEvent], tuple[BoundCallback, str]] = {}

        self.focused: Window | None = None
        self.autorun = autorun
        self.layout = layout_type()
        self.compositor = Compositor(self._windows, framerate=framerate)
        self.mouse_translator: MouseTranslator | None = None

        # This isn't quite implemented at the moment.
        self.restrict_within_bounds = True

        terminal.subscribe(terminal.RESIZE, self.on_resize)

    def __iadd__(self, other: object) -> WindowManager:
        """Adds a window to the manager."""

        if not isinstance(other, Window):
            raise ValueError("You may only add windows to a WindowManager.")

        return self.add(other)

    def __isub__(self, other: object) -> WindowManager:
        """Removes a window from the manager."""

        if not isinstance(other, Window):
            raise ValueError("You may only add windows to a WindowManager.")

        return self.remove(other)

    def __enter__(self) -> WindowManager:
        """Starts context manager."""

        return self

    def __exit__(self, _: Any, exception: Exception, __: Any) -> bool:
        """Ends context manager."""

        # Run the manager if it hasnt been run before.
        if self.autorun and exception is None and self.mouse_translator is None:
            self.run()

        if exception is not None:
            self.stop()
            raise exception

        return True

    def __iter__(self) -> Iterator[Window]:
        """Iterates this manager's windows."""

        return iter(self._windows)

    def _run_input_loop(self) -> None:
        """The main input loop of the WindowManager."""

        while self._is_running:
            key = getch(interrupts=False)

            if key == chr(3):
                self.stop()
                break

            if self.handle_key(key):
                continue

            self.process_mouse(key)

    def get_lines(self) -> list[str]:
        """Gets the empty list."""

        # TODO: Allow using WindowManager as a widget.

        return []

    def clear_cache(self, window: Window) -> None:
        """Clears the compositor's cache related to the given window."""

        self.compositor.clear_cache(window)

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

        self.layout.apply()
        self.compositor.redraw()

    def run(self, mouse_events: list[str] | None = None) -> None:
        """Starts the WindowManager.

        Args:
            mouse_events: A list of mouse event types to listen to. See
                `pytermgui.ansi_interface.report_mouse` for more information.
                Defaults to `["press_hold", "hover"]`.

        Returns:
            The WindowManager's compositor instance.
        """

        self._is_running = True

        if mouse_events is None:
            mouse_events = ["press_hold", "hover"]

        with alt_buffer(cursor=False, echo=False):
            with mouse_handler(mouse_events, "decimal_xterm") as translate:
                self.mouse_translator = translate
                self.compositor.run()

                self._run_input_loop()

    def stop(self) -> None:
        """Stops the WindowManager and its compositor."""

        self.compositor.stop()
        self._is_running = False

    def add(
        self, window: Window, assign: str | bool = True, animate: bool = True
    ) -> WindowManager:
        """Adds a window to the manager.

        Args:
            window: The window to add.
            assign: The name of the slot the new window should be assigned to, or a
                boolean. If it is given a str, it is treated as the name of a slot. When
                given True, the next non-filled slot will be assigned, and when given
                False no assignment will be done.
            animate: If set, an animation will be played on the window once it's added.
        """

        self._windows.insert(0, window)
        window.manager = self

        if assign:
            if isinstance(assign, str):
                getattr(self.layout, assign).content = window

            elif len(self._windows) <= len(self.layout.slots):
                self.layout.assign(window, index=len(self._windows) - 1)

            self.layout.apply()

        # New windows take focus-precedence over already
        # existing ones, even if they are modal.
        self.focus(window)

        if not animate:
            return self

        if window.height > 1:
            animator.animate_attr(
                target=window,
                attr="height",
                start=0,
                end=window.height,
                duration=300,
                on_step=_center_during_animation,
            )

        return self

    def remove(
        self,
        window: Window,
        autostop: bool = True,
        animate: bool = True,
    ) -> WindowManager:
        """Removes a window from the manager.

        Args:
            window: The window to remove.
            autostop: If set, the manager will be stopped if the length of its windows
                hits 0.
        """

        def _on_finish(_: AttrAnimation | None) -> bool:
            self._windows.remove(window)

            if autostop and len(self._windows) == 0:
                self.stop()
            else:
                self.focus(self._windows[0])

            return True

        if not animate:
            _on_finish(None)
            return self

        animator.animate_attr(
            target=window,
            attr="height",
            end=0,
            duration=300,
            on_step=_center_during_animation,
            on_finish=_on_finish,
        )

        return self

    def focus(self, window: Window | None) -> None:
        """Focuses a window by moving it to the first index in _windows."""

        if self.focused is not None:
            self.focused.blur()

        self.focused = window

        if window is not None:
            self._windows.remove(window)
            self._windows.insert(0, window)

            window.focus()

    def focus_next(self) -> Window | None:
        """Focuses the next window in focus order, looping to first at the end."""

        if self.focused is None:
            self.focus(self._windows[0])
            return self.focused

        index = self._windows.index(self.focused)
        if index == len(self._windows) - 1:
            index = 0

        window = self._windows[index]
        traversed = 0
        while window.is_persistent or window is self.focused:
            if index >= len(self._windows):
                index = 0

            window = self._windows[index]

            index += 1
            traversed += 1
            if traversed >= len(self._windows):
                return self.focused

        self.focus(self._windows[index])

        return self.focused

    def handle_key(self, key: str) -> bool:
        """Processes a keypress.

        Args:
            key: The key to handle.

        Returns:
            True if the given key could be processed, False otherwise.
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

    # I prefer having the _click, _drag and _release helpers within this function, for
    # easier readability.
    def process_mouse(self, key: str) -> None:  # pylint: disable=too-many-statements
        """Processes (potential) mouse input.

        Args:
            key: Input to handle.
        """

        window: Window

        def _clamp_pos(pos: tuple[int, int], index: int) -> int:
            """Clamp a value using index to address x/y & width/height"""

            offset = self._drag_offsets[index]

            # TODO: This -2 is a very magical number. Not good.
            maximum = terminal.size[index] - ((window.width, window.height)[index] - 2)

            start_margin_index = abs(index - 1)

            if self.restrict_within_bounds:
                return max(
                    index + terminal.margins[start_margin_index],
                    min(
                        pos[index] - offset,
                        maximum
                        - terminal.margins[start_margin_index + 2]
                        - terminal.origin[index],
                    ),
                )

            return pos[index] - offset

        def _click(pos: tuple[int, int], window: Window) -> bool:
            """Process clicking a window."""

            left, top, right, bottom = window.rect
            borders = window.chars.get("border", [" "] * 4)

            if real_length(borders[1]) > 0 and pos[1] == top and left <= pos[0] < right:
                self._drag_target = (window, Edge.TOP)

            elif (
                real_length(borders[3]) > 0
                and pos[1] == bottom - 1
                and left <= pos[0] < right
            ):
                self._drag_target = (window, Edge.BOTTOM)

            elif (
                real_length(borders[0]) > 0
                and pos[0] == left
                and top <= pos[1] < bottom
            ):
                self._drag_target = (window, Edge.LEFT)

            elif (
                real_length(borders[2]) > 0
                and pos[0] == right - 1
                and top <= pos[1] < bottom
            ):
                self._drag_target = (window, Edge.RIGHT)

            else:
                return False

            self._drag_offsets = (
                pos[0] - window.pos[0],
                pos[1] - window.pos[1],
            )

            return True

        def _drag(pos: tuple[int, int], window: Window) -> bool:
            """Process dragging a window"""

            if self._drag_target is None:
                return False

            target_window, edge = self._drag_target
            handled = False

            if window is not target_window:
                return False

            left, top, right, bottom = window.rect

            if not window.is_static and edge is Edge.TOP:
                window.pos = (
                    _clamp_pos(pos, 0),
                    _clamp_pos(pos, 1),
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

            if handled:
                window.is_dirty = True
                self.compositor.set_redraw()

            return handled

        def _release(_: tuple[int, int], __: Window) -> bool:
            """Process release of key"""

            self._drag_target = None

            # This return False so Window can handle the mouse action as well,
            # as not much is done in this callback.
            return False

        handlers = {
            MouseAction.LEFT_CLICK: _click,
            MouseAction.LEFT_DRAG: _drag,
            MouseAction.RELEASE: _release,
        }

        translate = self.mouse_translator
        event_list = None if translate is None else translate(key)

        if event_list is None:
            return

        for event in event_list:
            # Ignore null-events
            if event is None:
                continue

            for window in self._windows:
                contains = window.contains(event.position)

                if event.action in self.focusing_actions:
                    self.focus(window)

                if event.action in handlers and handlers[event.action](
                    event.position, window
                ):
                    break

                if window.handle_mouse(event) or (contains or window.is_modal):
                    break

            # Unset drag_target if no windows received the input
            else:
                self._drag_target = None

    def screenshot(self, title: str, filename: str = "screenshot.svg") -> None:
        """Takes a screenshot of the current state.

        See `pytermgui.exporters.to_svg` for more information.

        Args:
            filename: The name of the file.
        """

        self.compositor.capture(title=title, filename=filename)

    def show_positions(self) -> None:
        """Shows the positions of each Window's widgets."""

        def _show_positions(widget, color_base: int = 60) -> None:
            """Show positions of widget."""

            if isinstance(widget, Container):
                for i, subwidget in enumerate(widget):
                    _show_positions(subwidget, color_base + i)

                return

            if not widget.is_selectable:
                return

            debug = widget.debug()
            color = str_to_color(f"@{color_base}")
            buff = color(" ", reset=False)

            for i in range(min(widget.width, real_length(debug)) - 1):
                buff += debug[i]

            self.terminal.write(buff, pos=widget.pos)

        for widget in self._windows:
            _show_positions(widget)
        self.terminal.flush()

        getch()

    def alert(self, *items, center: bool = True, **attributes) -> Window:
        """Creates a modal popup of the given elements and attributes.

        Args:
            *items: All widget-convertable objects passed as children of the new window.
            center: If set, `pytermgui.window_manager.window.center` is called on the window.
            **attributes: kwargs passed as the new window's attributes.
        """

        window = Window(*items, is_modal=True, **attributes)

        if center:
            window.center()

        self.add(window, assign=False)

        return window

    def toast(
        self,
        *items,
        offset: int = 0,
        duration: int = 300,
        delay: int = 1000,
        **attributes,
    ) -> Window:
        """Creates a Material UI-inspired toast window of the given elements and attributes.

        Args:
            *items: All widget-convertable objects passed as children of the new window.
            delay: The amount of time before the window will start animating out.
            **attributes: kwargs passed as the new window's attributes.
        """

        # pylint: disable=no-value-for-parameter

        toast = Window(*items, is_noblur=True, **attributes)

        target_height = toast.height
        toast.overflow = Overflow.HIDE

        def _finish(_: Animation) -> None:
            self.remove(toast, animate=False)

        def _progressively_show(anim: Animation, invert: bool = False) -> bool:
            height = int(anim.state * target_height)

            toast.center()

            if invert:
                toast.height = target_height - 1 - height
                toast.pos = (
                    toast.pos[0],
                    self.terminal.height - toast.height + 1 - offset,
                )
                return False

            toast.height = height
            toast.pos = (toast.pos[0], self.terminal.height - toast.height + 1 - offset)

            return False

        def _animate_toast_out(_: Animation) -> None:
            animator.schedule(
                FloatAnimation(
                    delay,
                    on_finish=lambda *_: animator.schedule(
                        FloatAnimation(
                            duration,
                            on_step=lambda anim: _progressively_show(anim, invert=True),
                            on_finish=_finish,
                        )
                    ),
                )
            )

        leadup = FloatAnimation(
            duration, on_step=_progressively_show, on_finish=_animate_toast_out
        )

        # pylint: enable=no-value-for-parameter

        self.add(toast.center(), animate=False, assign=False)
        self.focus(toast)
        animator.schedule(leadup)

        return toast
