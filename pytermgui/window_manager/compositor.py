from __future__ import annotations

import time
from threading import Thread
from functools import lru_cache
from typing import TYPE_CHECKING
from itertools import zip_longest

from ..regex import strip_ansi
from ..parser import tim, TokenType
from ..animations import animator, Animation
from ..terminal import get_terminal, Terminal

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

            last_frame = time.perf_counter()

            animator.step()
            self.draw()
            framecount += 1

            if last_frame - fps_start_time >= 1:
                self.fps = framecount
                fps_start_time = last_frame
                framecount = 0

    def _get_lines(self, window: Window) -> list[str]:
        """Gets lines from the window, caching when possible."""

        if window.allow_fullscreen:
            window.pos = self.terminal.origin
            window.width = self.terminal.width + 1
            window.height = self.terminal.height + 1

        _id = id(window)
        if window.has_focus or window.is_noblur:
            return window.get_lines()

        if not window.is_dirty and _id in self._cache:
            return self._cache[_id]

        lines = []
        for line in window.get_lines():
            if not window.has_focus:
                line = tim.parse("[239]" + strip_ansi(line))

            lines.append(line)

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

        # Don't unnecessarily print under full screen windows
        if any(window.allow_fullscreen for window in self._windows):
            for window in reversed(self._windows):
                if window.allow_fullscreen:
                    windows = [window]
                    break

        else:
            windows = self._windows

        for window in reversed(windows):
            for i, line in enumerate(self._get_lines(window)):
                pos = (window.pos[0], window.pos[1] + i)
                lines.append((pos, line))

            if window.allow_fullscreen:
                break

        return lines

    def draw(self) -> None:
        """Writes composited screen to the terminal.

        Steps:
        - Composite screen
        - TODO: Get difference of current composite against the previous
        - Write difference to the terminal
        """

        lines = self.composite()
        if self._previous == lines:
            return

        self.terminal.clear_stream()
        for (pos, line) in lines:
            self.terminal.write(line, pos=pos)

        self.terminal.flush()

        self._previous = lines

    def capture(self, title: str, filename: str | None = None) -> None:
        """Captures the most-recently drawn buffer as `filename`.

        See `pytermgui.exporters.to_svg` for more information.
        """

        with self.terminal.record() as recording:
            for (pos, line) in self._previous:
                self.terminal.write(line, pos=pos)

        recording.save_svg(title=title, filename=filename)
        self.draw()
