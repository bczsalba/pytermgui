"""The Compositor class, which is used by the WindowManager to draw onto the terminal."""

# pylint: disable=too-many-instance-attributes

from __future__ import annotations

import time
from threading import Thread
from typing import Iterator, List, Tuple

from ..widgets import Widget
from ..enums import WidgetChange
from ..animations import animator
from ..terminal import get_terminal, Terminal

from .window import Window

PositionedLineList = List[Tuple[Tuple[int, int], str]]


class Compositor:
    """The class used to draw `pytermgui.window_managers.manager.WindowManager` state.

    This class handles turning a list of windows into a drawable buffer (composite),
    and then drawing it onto the screen.

    Calling its `run` method will start the drawing thread, which will draw the current
    window states onto the screen. This routine targets `framerate`, though will likely
    not match it perfectly.
    """

    def __init__(self, windows: list[Window], framerate: int) -> None:
        """Initializes the Compositor.

        Args:
            windows: A list of the windows to be drawn.
        """

        self._windows = windows
        self._is_running = False

        self._previous: PositionedLineList = []
        self._frametime = 0.0
        self._should_redraw: bool = True
        self._cache: dict[int, list[str]] = {}

        self.fps = 0
        self.framerate = framerate

    @property
    def terminal(self) -> Terminal:
        """Returns the current global terminal."""

        return get_terminal()

    def _draw_loop(self) -> None:
        """A loop that draws at regular intervals."""

        framecount = 0
        last_frame = fps_start_time = time.perf_counter()

        while self._is_running:
            elapsed = time.perf_counter() - last_frame

            if elapsed < self._frametime:
                time.sleep(self._frametime - elapsed)
                continue

            animator.step(elapsed)

            last_frame = time.perf_counter()
            self.draw()

            framecount += 1

            if last_frame - fps_start_time >= 1:
                self.fps = framecount
                fps_start_time = last_frame
                framecount = 0

    # NOTE: This is not needed at the moment, but might be at some point soon.
    # def _get_lines(self, window: Window) -> list[str]:
    #     """Gets lines from the window, caching when possible.

    #     This also applies the blurred style of the window, if it has no focus.
    #     """

    #     if window.allow_fullscreen:
    #         window.pos = self.terminal.origin
    #         window.width = self.terminal.width
    #         window.height = self.terminal.height

    #     return window.get_lines()

    #     if window.has_focus or window.is_noblur:
    #         return window.get_lines()

    #     _id = id(window)
    #     if not window.is_dirty and _id in self._cache:
    #         return self._cache[_id]

    #     lines: list[str] = []
    #     for line in window.get_lines():
    #         if not window.has_focus:
    #             line = tim.parse("[239]" + strip_ansi(line).replace("[", r"\["))

    #         lines.append(line)

    #     self._cache[_id] = lines
    #     return lines

    @staticmethod
    def _iter_positioned(
        widget: Widget, until: int | None = None
    ) -> Iterator[tuple[tuple[int, int], str]]:
        """Iterates through (pos, line) tuples from widget.get_lines()."""

        # get_lines = widget.get_lines
        # if isinstance(widget, Window):
        #     get_lines = lambda *_: self._get_lines(widget)  # type: ignore

        if until is None:
            until = widget.height

        for i, line in enumerate(widget.get_lines()):
            if i >= until:
                break

            pos = (widget.pos[0], widget.pos[1] + i)

            yield (pos, line)

    @property
    def framerate(self) -> int:
        """The framerate the draw loop runs at.

        Note:
            This will likely not be matched very accurately, mostly undershooting
            the given target.
        """

        return self._framerate

    @framerate.setter
    def framerate(self, new: int) -> None:
        """Updates the framerate."""

        self._frametime = 1 / new
        self._framerate = new

    def clear_cache(self, window: Window) -> None:
        """Clears the compositor's cache related to the given window."""

        if id(window) in self._cache:
            del self._cache[id(window)]

    def run(self) -> None:
        """Runs the compositor draw loop as a thread."""

        self._is_running = True
        Thread(name="CompositorDrawLoop", target=self._draw_loop).start()

    def stop(self) -> None:
        """Stops the compositor."""

        self._is_running = False

    def composite(self) -> PositionedLineList:
        """Creates a composited buffer from the assigned windows.

        Note that this is currently not used."""

        lines = []
        windows = self._windows

        # Don't unnecessarily print under full screen windows
        if any(window.allow_fullscreen for window in self._windows):
            for window in reversed(self._windows):
                if window.allow_fullscreen:
                    windows = [window]
                    break

        size_changes = {WidgetChange.WIDTH, WidgetChange.HEIGHT, WidgetChange.SIZE}
        for window in reversed(windows):
            if not window.has_focus:
                continue

            change = window.get_change()

            if change is None:
                continue

            if window.is_dirty or change in size_changes:
                for pos, line in self._iter_positioned(window):
                    lines.append((pos, line))

                window.is_dirty = False
                continue

            if change is not None:
                remaining = window.content_dimensions[1]

                for widget in window.dirty_widgets:
                    for pos, line in self._iter_positioned(widget, until=remaining):
                        lines.append((pos, line))

                    remaining -= widget.height

                window.dirty_widgets = []
                continue

            if window.allow_fullscreen:
                break

        return lines

    def set_redraw(self) -> None:
        """Flags compositor for full redraw.

        Note:
            At the moment the compositor will always redraw the entire screen.
        """

        self._should_redraw = True

    def draw(self, force: bool = False) -> None:
        """Writes composited screen to the terminal.

        At the moment this uses full-screen rewrites. There is a compositing
        implementation in `composite`, but it is currently not performant enough to use.

        Args:
            force: When set, new composited lines will not be checked against the
                previous ones, and everything will be redrawn.
        """

        # if self._should_redraw or force:
        lines: PositionedLineList = []

        for window in reversed(self._windows):
            lines.extend(self._iter_positioned(window))

        self._should_redraw = False

        # else:
        # lines = self.composite()

        if not force and self._previous == lines:
            return

        buffer = "".join(f"\x1b[{pos[1]};{pos[0]}H{line}" for pos, line in lines)

        self.terminal.clear_stream()
        self.terminal.write(buffer)
        self.terminal.flush()

        self._previous = lines

    def redraw(self) -> None:
        """Force-redraws the buffer."""

        self.draw(force=True)

    def capture(self, title: str, filename: str | None = None) -> None:
        """Captures the most-recently drawn buffer as `filename`.

        See `pytermgui.exporters.to_svg` for more information.
        """

        with self.terminal.record() as recording:
            self.redraw()

        recording.save_svg(title=title, filename=filename)
