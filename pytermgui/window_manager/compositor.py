from __future__ import annotations

import time
from threading import Thread
from functools import lru_cache
from typing import TYPE_CHECKING
from itertools import zip_longest

from ..regex import strip_ansi
from ..terminal import terminal
from ..parser import tim, TokenType
from ..animations import animator, Animation

from .window import Window


class Compositor:
    def __init__(self, windows: list[Window], framerate: int) -> None:
        """Initializes the Compositor.

        Args:
            windows: A list of the windows to be drawn.
        """

        self._windows = windows
        self._is_running = False

        self._frametime = 0
        self._previous = ""
        self._cache: dict[int, list[str]] = {}

        self.framerate = framerate

    def _draw_loop(self) -> None:
        """A loop that draws at regular intervals."""

        last_frame = fps_start_time = time.perf_counter()
        framecount = 0
        while self._is_running:
            elapsed = time.perf_counter() - last_frame
            if elapsed < self._frametime:
                time.sleep(self._frametime - elapsed)
                framecount += 1
                continue

            animator.step()
            self.draw()

            last_frame = time.perf_counter()

            if last_frame - fps_start_time >= 1:
                self.fps = framecount
                fps_start_time = last_frame
                framecount = 0

            framecount += 1

    def _get_lines(self, window: Window) -> list[str]:
        """Gets lines from the window, caching when possible."""

        _id = id(window)
        if window.has_focus or window.is_noblur:
            return window.get_lines()

        if not window.is_dirty and _id in self._cache:
            return self._cache[_id]

        lines = window.get_lines()

        if not window.has_focus:
            for i, line in enumerate(lines):
                lines[i] = tim.parse("[239]" + strip_ansi(line))

        self._cache[_id] = lines
        return lines

    @property
    def framerate(self) -> int:
        """The framerate the draw loop runs at."""

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

    def composite(self) -> str:
        """Composites the windows into one string."""

        lines = []
        for window in reversed(self._windows):
            for i, line in enumerate(self._get_lines(window)):
                pos = (window.pos[0], window.pos[1] + i)
                lines.append((pos, line))

        return lines

    def draw(self) -> None:
        """Writes composited screen to the terminal.

        Steps:
        - Composite screen
        - Get difference of current composite against the previous
        - Write difference to the terminal
        """

        lines = self.composite()
        if self._previous == lines:
            return

        terminal.clear_stream()
        for (pos, line) in lines:
            terminal.write(line, pos=pos)

        terminal.flush()

        self._previous = lines

    def capture(self, title: str, filename: str | None = None) -> None:
        """Captures the most-recently drawn buffer as `filename`.

        See `pytermgui.exporters.to_svg` for more information.
        """

        with terminal.record() as recording:
            for (pos, line) in self._previous:
                terminal.write(line, pos=pos)

        recording.save_svg(title=title, filename=filename)
        self.draw()
