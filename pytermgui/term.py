"""This module houses the `Terminal` class, and its provided instance."""

# pylint: disable=cyclic-import

from __future__ import annotations

import errno
import os
import signal
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from functools import cached_property
from io import StringIO
from shutil import get_terminal_size
from typing import TYPE_CHECKING, Any, Callable, Generator, TextIO

from .input import getch_timeout
from .regex import RE_PIXEL_SIZE, has_open_sequence, real_length, strip_ansi

if TYPE_CHECKING:
    from .fancy_repr import FancyYield

__all__ = [
    "terminal",
    "set_global_terminal",
    "get_terminal",
    "Terminal",
    "Recorder",
    "ColorSystem",
]


class Recorder:
    """A class that records & exports terminal content."""

    def __init__(self) -> None:
        """Initializes the Recorder."""

        self.recording: list[tuple[str, float]] = []
        self._start_stamp = time.time()

    @property
    def _content(self) -> str:
        """Returns the str part of self._recording"""

        return "".join(data for data, _ in self.recording)

    def write(self, data: str) -> None:
        """Writes to the recorder."""

        self.recording.append((data, time.time() - self._start_stamp))

    def export_text(self) -> str:
        """Exports current content as plain text."""

        return strip_ansi(self._content)

    def export_html(
        self, prefix: str | None = None, inline_styles: bool = False
    ) -> str:
        """Exports current content as HTML.

        For help on the arguments, see `pytermgui.html.to_html`.
        """

        from .exporters import to_html  # pylint: disable=import-outside-toplevel

        return to_html(self._content, prefix=prefix, inline_styles=inline_styles)

    def export_svg(
        self,
        prefix: str | None = None,
        inline_styles: bool = False,
        title: str = "PyTermGUI",
        chrome: bool = True,
    ) -> str:
        """Exports current content as SVG.

        For help on the arguments, see `pytermgui.html.to_svg`.
        """

        from .exporters import to_svg  # pylint: disable=import-outside-toplevel

        return to_svg(
            self._content,
            prefix=prefix,
            inline_styles=inline_styles,
            title=title,
            chrome=chrome,
        )

    def save_plain(self, filename: str) -> None:
        """Exports plain text content to the given file.

        Args:
            filename: The file to save to.
        """

        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.export_text())

    def save_html(
        self,
        filename: str | None = None,
        prefix: str | None = None,
        inline_styles: bool = False,
    ) -> None:
        """Exports HTML content to the given file.

        For help on the arguments, see `pytermgui.exporters.to_html`.

        Args:
            filename: The file to save to. If the filename does not contain the '.html'
                extension it will be appended to the end.
        """

        if filename is None:
            filename = f"PTG_{time.time():%Y-%m-%d %H:%M:%S}.html"

        if not filename.endswith(".html"):
            filename += ".html"

        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.export_html(prefix=prefix, inline_styles=inline_styles))

    def save_svg(  # pylint: disable=too-many-arguments
        self,
        filename: str | None = None,
        prefix: str | None = None,
        chrome: bool = True,
        inline_styles: bool = False,
        title: str = "PyTermGUI",
    ) -> None:
        """Exports SVG content to the given file.

        For help on the arguments, see `pytermgui.exporters.to_svg`.

        Args:
            filename: The file to save to. If the filename does not contain the '.svg'
                extension it will be appended to the end.
        """

        if filename is None:
            timeval = datetime.now()
            filename = f"PTG_{timeval:%Y-%m-%d_%H:%M:%S}.svg"

        if not filename.endswith(".svg"):
            filename += ".svg"

        with open(filename, "w", encoding="utf-8") as file:
            file.write(
                self.export_svg(
                    prefix=prefix,
                    inline_styles=inline_styles,
                    title=title,
                    chrome=chrome,
                )
            )


class ColorSystem(Enum):
    """An enumeration of various terminal-supported colorsystems."""

    NO_COLOR = -1
    """No-color terminal. See https://no-color.org/."""

    STANDARD = 0
    """Standard 3-bit colorsystem of the basic 16 colors."""

    EIGHT_BIT = 1
    """xterm 8-bit colors, 0-256."""

    TRUE = 2
    """'True' color, a.k.a. 24-bit RGB colors."""

    def __ge__(self, other):
        """Comparison: self >= other."""

        if self.__class__ is other.__class__:
            return self.value >= other.value

        return NotImplemented

    def __gt__(self, other):
        """Comparison: self > other."""

        if self.__class__ is other.__class__:
            return self.value > other.value

        return NotImplemented

    def __le__(self, other):
        """Comparison: self <= other."""

        if self.__class__ is other.__class__:
            return self.value <= other.value

        return NotImplemented

    def __lt__(self, other):
        """Comparison: self < other."""

        if self.__class__ is other.__class__:
            return self.value < other.value

        return NotImplemented


def _get_env_colorsys() -> ColorSystem | None:
    """Gets a colorsystem if the `PTG_COLOR_SYSTEM` env var can be linked to one."""

    colorsys = os.getenv("PTG_COLOR_SYSTEM")
    if colorsys is None:
        return None

    try:
        return ColorSystem[colorsys]

    except NameError:
        return None


class Terminal:  # pylint: disable=too-many-instance-attributes
    """A class to store & access data about a terminal."""

    RESIZE = 0
    """Event sent out when the terminal has been resized.

    Arguments passed:
    - New size: tuple[int, int]
    """

    margins = [0, 0, 0, 0]
    """Not quite sure what this does at the moment."""

    displayhook_installed: bool = False
    """This is set to True when `pretty.install` is called."""

    origin: tuple[int, int] = (1, 1)
    """Origin of the internal coordinate system."""

    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        size: tuple[int, int] | None = None,
    ) -> None:
        """Initialize `Terminal` class."""

        if stream is None:
            stream = sys.stdout

        self._size = size
        self._stream = stream or sys.stdout

        self._recorder: Recorder | None = None

        self.size: tuple[int, int] = self._get_size()
        self.forced_colorsystem: ColorSystem | None = _get_env_colorsys()

        self._listeners: dict[int, list[Callable[..., Any]]] = {}

        if hasattr(signal, "SIGWINCH"):
            signal.signal(signal.SIGWINCH, self._update_size)
        else:
            from threading import Thread  # pylint: disable=import-outside-toplevel

            Thread(
                name="windows_terminal_resize",
                target=self._window_terminal_resize,
                daemon=True,
            ).start()

        self._diff_buffer = [
            ["" for _ in range(self.width)] for y in range(self.height)
        ]

    def _window_terminal_resize(self):
        from time import sleep  # pylint: disable=import-outside-toplevel

        _previous = get_terminal_size()
        while True:
            _next = get_terminal_size()
            if _previous != _next:
                self._update_size()
                _previous = _next
            sleep(0.001)

    def __fancy_repr__(self) -> Generator[FancyYield, None, None]:
        """Returns a cool looking repr."""

        name = type(self).__name__

        yield f"<{name} stream={self._stream} size={self.size}>"

    @cached_property
    def resolution(self) -> tuple[int, int]:
        """Returns the terminal's pixel based resolution.

        Only evaluated on demand.
        """

        if self.isatty():
            sys.stdout.write("\x1b[14t")
            sys.stdout.flush()

            # Some terminals may not respond to a pixel size query, so we send
            # a timed-out getch call with a default response of 1280x720.
            output = getch_timeout(0.1, default="\x1b[4;720;1280t")
            match = RE_PIXEL_SIZE.match(output)

            if match is not None:
                return (int(match[2]), int(match[1]))

        return (0, 0)

    @property
    def pixel_size(self) -> tuple[int, int]:
        """DEPRECATED: Returns the terminal's pixel resolution.

        Prefer terminal.resolution.
        """

        return self.resolution

    def _call_listener(self, event: int, data: Any) -> None:
        """Calls callbacks for event.

        Args:
            event: A terminal event.
            data: Arbitrary data passed to the callback.
        """

        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(data)

    def _get_size(self) -> tuple[int, int]:
        """Gets the screen size with origin substracted."""

        if self._size is not None:
            return self._size

        size = get_terminal_size()
        return (size[0], size[1])

    def _update_size(self, *_: Any) -> None:
        """Resize terminal when SIGWINCH occurs, and call listeners."""

        if hasattr(self, "resolution"):
            del self.resolution

        self.size = self._get_size()

        self._call_listener(self.RESIZE, self.size)

        # Wipe the screen in case anything got messed up
        self.write("\x1b[2J")

    @property
    def width(self) -> int:
        """Gets the current width of the terminal."""

        return self.size[0]

    @property
    def height(self) -> int:
        """Gets the current height of the terminal."""

        return self.size[1]

    @staticmethod
    def is_interactive() -> bool:
        """Determines whether shell is interactive.

        A shell is interactive if it is run from `python3` or `python3 -i`.
        """

        return hasattr(sys, "ps1")

    @property
    def forced_colorsystem(self) -> ColorSystem | None:
        """Forces a color system type on this terminal."""

        return self._forced_colorsystem

    @forced_colorsystem.setter
    def forced_colorsystem(self, new: ColorSystem | None) -> None:
        """Sets a colorsystem, clears colorsystem cache."""

        self._forced_colorsystem = new

    @property
    def colorsystem(self) -> ColorSystem:
        """Gets the current terminal's supported color system."""

        if self.forced_colorsystem is not None:
            return self.forced_colorsystem

        if os.getenv("NO_COLOR") is not None:
            return ColorSystem.NO_COLOR

        term = os.getenv("TERM", "")
        color_term = os.getenv("COLORTERM", "").strip().lower()

        if color_term == "":
            color_term = term.split("xterm-")[-1]

        if color_term in ["24bit", "truecolor"]:
            return ColorSystem.TRUE

        if color_term == "256color":
            return ColorSystem.EIGHT_BIT

        return ColorSystem.STANDARD

    @contextmanager
    def record(self) -> Generator[Recorder, None, None]:
        """Records the terminal's stream."""

        if self._recorder is not None:
            raise RuntimeError(f"{self!r} is already recording.")

        try:
            self._recorder = Recorder()
            yield self._recorder

        finally:
            self._recorder = None

    @contextmanager
    def no_record(self) -> Generator[None, None, None]:
        """Pauses recording for the duration of the context."""

        recorder = self._recorder

        try:
            self._recorder = None
            yield

        finally:
            self._recorder = recorder

    @contextmanager
    def frame(self) -> Generator[StringIO, None, None]:
        """Notifies the emulator of the inner content being a single frame.

        See https://gist.github.com/christianparpart/d8a62cc1ab659194337d73e399004036!
        """

        buffer = StringIO()

        try:
            with self.no_record():
                self.write("\x1b[?2026h")
            yield buffer

        finally:
            self.write(buffer.getvalue())
            with self.no_record():
                self.write("\x1b[?2026l")
            self.flush()

    @staticmethod
    def isatty() -> bool:
        """Returns whether sys.stdin is a tty."""

        return sys.stdin.isatty()

    def replay(self, recorder: Recorder) -> None:
        """Replays a recording."""

        last_time = 0.0
        for data, delay in recorder.recording:
            if last_time > 0.0:
                time.sleep(delay - last_time)

            self.write(data, flush=True)
            last_time = delay

    def subscribe(self, event: int, callback: Callable[..., Any]) -> None:
        """Subcribes a callback to be called when event occurs.

        Args:
            event: The terminal event that calls callback.
            callback: The callable to be called. The signature of this
                callable is dependent on the event. See the documentation
                of the specific event for more information.
        """

        if not event in self._listeners:
            self._listeners[event] = []

        self._listeners[event].append(callback)

    def write(
        self,
        data: str,
        pos: tuple[int, int] | None = None,
        flush: bool = False,
        slice_too_long: bool = True,
    ) -> None:
        """Writes the given data to the terminal's stream.

        Args:
            data: The data to write.
            pos: Terminal-character space position to write the data to, (x, y).
            flush: If set, `flush` will be called on the stream after reading.
            slice_too_long: If set, lines that are outside of the terminal will be
                sliced to fit. Involves a sizable performance hit.
        """

        def _slice(line: str, maximum: int) -> str:
            length = 0
            sliced = ""
            for char in line:
                sliced += char
                if char == "\x1b":
                    continue

                if (
                    length > maximum
                    and real_length(sliced) > maximum
                    and not has_open_sequence(sliced)
                ):
                    break

                length += 1

            return sliced

        if "\x1b[2J" in data:
            self.clear_stream()

        if pos is not None:
            xpos, ypos = pos
            xpos += self.origin[0]
            ypos += self.origin[1]

            if slice_too_long:
                if not self.height + self.origin[1] + 1 > ypos >= 0:
                    return

                maximum = self.width - xpos

                if xpos < self.origin[0]:
                    xpos = self.origin[0]

                sliced = _slice(data, maximum) if len(data) > maximum else data

                data = f"\x1b[{ypos};{xpos}H{sliced}\x1b[0m"

            else:
                data = f"\x1b[{ypos};{xpos}H{data}"

        self._stream.write(data)

        if self._recorder is not None:
            self._recorder.write(data)

        if flush:
            self._stream.flush()

    def clear_stream(self) -> None:
        """Clears (truncates) the terminal's stream."""

        try:
            self._stream.truncate(0)

        except OSError as error:
            if error.errno != errno.EINVAL and os.name != "nt":
                raise

        self._stream.write("\x1b[2J")

    def print(
        self,
        *items,
        pos: tuple[int, int] | None = None,
        sep: str = " ",
        end="\n",
        flush: bool = True,
    ) -> None:
        """Prints items to the stream.

        All arguments not mentioned here are analogous to `print`.

        Args:
            pos: Terminal-character space position to write the data to, (x, y).

        """

        self.write(sep.join(map(str, items)) + end, pos=pos, flush=flush)

    def flush(self) -> None:
        """Flushes self._stream."""

        self._stream.flush()


terminal = Terminal()  # pylint: disable=invalid-name
"""Terminal instance that should be used pretty much always."""


def set_global_terminal(new: Terminal) -> None:
    """Sets the terminal instance to be used by the module."""

    globals()["terminal"] = new


def get_terminal() -> Terminal:
    """Gets the default terminal instance used by the module."""

    return terminal
