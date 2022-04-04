import time
from threading import Thread
from functools import lru_cache
from typing import TYPE_CHECKING
from itertools import zip_longest

from ..regex import strip_ansi
from ..terminal import terminal
from ..animations import animator
from ..parser import tim, TokenType

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
            # if not self.should_print:
            #     self._sleep(frametime)
            #     framecount += 1
            #     continue

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

    def run(self) -> None:
        """Runs the compositor draw loop as a thread."""

        self._is_running = True
        Thread(name="CompositorDrawLoop", target=self._draw_loop).start()

    def stop(self) -> None:
        """Stops the compositor."""

        self._is_running = False

    def composite(self) -> str:
        """Composites the windows into one string."""

        buffer = "\033[2J"
        for window in reversed(self._windows):
            for i, line in enumerate(self._get_lines(window)):
                pos = (window.pos[0], window.pos[1] + i)
                buffer += "\x1b[{};{}H".format(*reversed(pos))
                buffer += line

        return buffer

    def diff_buffers(
        self, seq1: str, seq2: str, start: tuple[int, int] = (0, 0)
    ) -> tuple[str, str]:
        """Gets the difference and merge of two ANSI-sequences.

        This is used in order to massively optimize printing routines,
        by only updating the characters that have changed since last
        print.

        **Note** that this method highly depends on the correct usage of
        positioning sequences.

        Args:
            seq1: The first (starting) sequence.
            seq2: The second (updated) sequence.
            start: The initial cursor position. Useful when the sequences
                are not supposed to be printed to the top-left corner.

        Returns:
            A tuple of (difference, merged). The difference can be used
            to update the screen state, and the merged value can be stored
            as the `seq1` value to use next.
        """

        def _as_matrix(seq: str) -> list[list[str]]:
            """Converts given sequence to a position-based matrix of strings.

            Args:
                seq: The string to convert.

            Returns:
                A variable height & length matrix defined as rows of chars. The
                dimensions of the matrix correspond to the ones defined in the
                string.
            """

            current_pos = list(start)

            output = []
            sequence_buffer = ""

            for token in tim.tokenize_ansi(seq):
                if token.ttype is TokenType.POSITION:
                    current_pos = [int(val) for val in token.data.split(",")]
                    continue

                # Pad rows
                xpos, ypos = current_pos

                if ypos >= len(output):
                    for _ in range(ypos - len(output) + 1):
                        output.append([])
                row = output[ypos]

                if token.ttype is not TokenType.PLAIN:
                    sequence_buffer += token.sequence
                    continue

                for char in token.data:
                    # Pad current row
                    if xpos >= len(row):
                        for _ in range(xpos - len(row) + 1):
                            row.append("")

                    row[xpos] += sequence_buffer + char
                    # row[xpos] += char
                    # xpos += 1

                current_pos = [xpos, ypos]

            return output

        def _to_sequence(matrix: list[list[str]]) -> str:
            """Returns an ANSI-sequence representation of the given matrix.

            The output sequence will use as little ANSI codes as possible, and
            in general tries to optimize out as much junk as it can.

            Returns:
                An ANSI-sequence representation of the given matrix.
            """

            current_pos = list(start)
            previous_pos = current_pos.copy()

            buff = ""
            for row in matrix:
                for char in row:
                    if char == "":
                        current_pos[0] += 1
                        continue

                    if not current_pos == previous_pos:
                        buff += "\x1b[{};{}H".format(*reversed(current_pos))

                    buff += char
                    current_pos[0] += 1
                    previous_pos = current_pos.copy()

                current_pos[1] += 1
                current_pos[0] = 0

            return (
                "\x1b[{};{}H".format(*reversed(current_pos)) + buff
                if len(buff) > 0
                else ""
            )

        mat1 = _as_matrix(seq1)
        mat2 = _as_matrix(seq2)

        output = []
        for i in range(max(len(mat1), len(mat2))):
            row1 = mat1[i] if len(mat1) > i else []
            row2 = mat2[i] if len(mat2) > i else []
            output.append([""] * max([len(row1), len(row2)]))

        for row, (row1, row2) in enumerate(zip_longest(mat1, mat2, fillvalue="")):
            for char, (char1, char2) in enumerate(
                zip_longest(row1, row2, fillvalue=None)
            ):
                if char2 is not None and char1 != char2:
                    output[row][char] = char2

        return _to_sequence(output)

    def draw(self) -> None:
        """Writes composited screen to the terminal.

        Steps:
            - Composite screen
            - Get difference of current composite against the previous
            - Write difference to the terminal
        """

        buffer = self.composite()
        if self._previous == buffer:
            return

        difference = buffer  # self.diff_buffers(self._previous, buffer)
        self._previous = buffer

        terminal.write(difference, flush=True)
