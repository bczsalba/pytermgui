"""This module contains the `InputField` class."""

from __future__ import annotations

import string
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Iterator, Literal

from wcwidth import wcwidth

from ..ansi_interface import MouseAction, MouseEvent
from ..enums import HorizontalAlignment
from ..helpers import break_line
from ..input import keys
from . import styles as w_styles
from .base import Widget


@dataclass
class Cursor(Iterable):
    """A simple dataclass representing the InputField's cursor."""

    row: int
    col: int

    def __iadd__(self, difference: tuple[int, int]) -> Cursor:
        """Move the cursor by the difference."""

        row, col = difference

        self.row += row
        self.col += col

        return self

    def __iter__(self) -> Iterator[int]:
        return iter((self.row, self.col))

    def __len__(self) -> int:
        return 2


class InputField(Widget):  # pylint: disable=too-many-instance-attributes
    """An element to display user input"""

    styles = w_styles.StyleManager(
        value="",
        prompt="surface+2",
        cursor="@primary dim #auto",
    )

    keys = {
        "move_left": {keys.LEFT},
        "move_right": {keys.RIGHT},
        "move_word_left": {keys.ALT_LEFT, keys.CTRL_LEFT},
        "move_word_right": {keys.ALT_RIGHT, keys.CTRL_RIGHT},
        "move_up": {keys.UP},
        "move_down": {keys.DOWN},
        "move_end": {keys.END},
        "move_home": {keys.HOME},
        "select_left": {keys.SHIFT_LEFT},
        "select_right": {keys.SHIFT_RIGHT},
        "select_up": {keys.SHIFT_UP},
        "select_down": {keys.SHIFT_DOWN},
        "word_remove": {keys.ALT_BACKSPACE, keys.CTRL_BACKSPACE},
    }

    parent_align = HorizontalAlignment.LEFT

    def __init__( # pylint: disable=too-many-arguments
        self,
        value: str = "",
        *,
        prompt: str = "",
        tablength: int = 4,
        multiline: bool = False,
        cursor: Cursor | None = None,
        **attrs: Any,
    ) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        if "width" not in attrs:
            self.width = len(value)

        if any(wcwidth(char) > 1 for char in value):
            raise ValueError("InputField doesn't support wide unicode characters.")

        self.prompt = prompt
        self.height = 1
        self.tablength = tablength
        self.multiline = multiline

        self.cursor = cursor or Cursor(0, len(value))

        self._lines = value.splitlines() or [""]
        self._selection_length = 1

        self._styled_cache: list[str] | None = self._style_and_break_lines()

        self._cached_state: int = self.width
        self._drag_start: tuple[int, int] | None = None

    @property
    def selectables_length(self) -> int:
        """Get length of selectables in object"""

        return 1

    @property
    def value(self) -> str:
        """Returns the internal value of this field."""

        return "\n".join(self._lines)

    @property
    def selection(self) -> str:
        """Returns the currently selected span of text."""

        start, end = sorted([self.cursor.col, self.cursor.col + self._selection_length])
        return self._lines[self.cursor.row][start:end]

    def _cache_is_valid(self) -> bool:
        """Determines if the styled line cache is still usable."""

        return self.width == self._cached_state

    def _style_and_break_lines(self) -> list[str]:
        """Styles and breaks self._lines."""

        document = (
            self.styles.prompt(self.prompt) + self.styles.value(self.value)
        ).splitlines()

        lines: list[str] = []
        width = self.width
        extend = lines.extend

        for line in document:
            extend(break_line(line.replace("\n", "\\n"), width, fill=" "))
            extend("")

        return lines

    def update_selection(self, count: int, correct_zero_length: bool = True) -> None:
        """Updates the selection state.

        Args:
            count: How many characters the cursor should change by. Negative for
                selecting leftward, positive for right.
            correct_zero_length: If set, when the selection length is 0 both the cursor
                and the selection length are manipulated to keep the original selection
                start while moving the selection in more of the way the user might
                expect.
        """

        self._selection_length += count

        if correct_zero_length and abs(self._selection_length) == 0:
            self._selection_length += 2 if count > 0 else -2
            self.move_cursor((0, (-1 if count > 0 else 1)))

    def delete_back(self, count: int = 1) -> str:
        """Deletes `count` characters from the cursor, backwards.

        Args:
            count: How many characters should be deleted.

        Returns:
            The deleted string.
        """

        row, col = self.cursor

        if len(self._lines) <= row:
            return ""

        line = self._lines[row]

        start, end = sorted([col, col - count])
        start = max(0, start)
        self._lines[row] = line[:start] + line[end:]

        self._styled_cache = None

        if self._lines[row] == "":
            self.move_cursor((0, -2))

            return self._lines.pop(row)

        if count > 0:
            self.move_cursor((0, -count))

        return line[col - count : col]

    def insert_text(self, text: str) -> None:
        """Inserts text at the cursor location."""

        row, col = self.cursor

        if len(self._lines) <= row:
            self._lines.insert(row, "")

        line = self._lines[row]

        self._lines[row] = line[:col] + text + line[col:]
        self.move_cursor((0, len(text)))

        self._styled_cache = None

    def get_word_pos(self, direction: Literal[-1, 1]) -> int:
        """Gets the column offset to the next word in the given direction.

        Args:
            direction: Which direction we need to look for.

        Returns:
            The column offset.
        """

        row, col = self.cursor
        if len(self._lines) <= row:
            return direction

        # Consistent with unix shell behaviour:
        # * Always delete first char, then remove any non-punctuation
        # Note that the exact behaviour isn't standardized:
        # * Python repl: until change in letter+digit & punctionation
        # * Unix shells: only removes letter+digit
        word_chars = string.ascii_letters + string.digits

        if direction == -1:
            line = self._lines[row][: col - 1]
            strip_line = line.rstrip(word_chars)

        else:
            line = self._lines[row][col:]
            strip_line = line.lstrip(word_chars)

        return -direction * (len(strip_line) - len(line)) + direction

    def handle_action(self, action: str) -> bool:
        """Handles some action.

        This will be expanded in the future to allow using all behaviours with
        just their actions.
        """

        cursors = {
            "move_left": (0, -1),
            "move_right": (0, 1),
            "move_up": (-1, 0),
            "move_down": (1, 0),
        }

        if action.startswith("move_"):
            if action.endswith(("word_left", "word_right")):
                col = self.get_word_pos(-1 if action == "move_word_left" else 1)
                self.move_cursor((0, col))
                return True

            if action.endswith(("end", "home")):
                crow, ccol = self.cursor
                if action == "move_end":
                    ccol = len(self._lines[crow])
                else:
                    ccol = 0
                self.move_cursor((crow, ccol), absolute=True)
                return True

            row, col = cursors[action]

            if self.cursor.row + row > len(self._lines):
                self._lines.append("")

            col += self._selection_length
            if self._selection_length > 0:
                col -= 1

            self._selection_length = 1
            self.move_cursor((row, col))
            return True

        if action.startswith("select_"):
            if action == "select_right":
                self.update_selection(1)

            elif action == "select_left":
                self.update_selection(-1)

            return True

        if action == "word_remove":
            row, col = self.cursor
            self.delete_back(-self.get_word_pos(-1))
            return True

        return False

    # TODO: This could probably be simplified by a wider adoption of the action pattern.
    def handle_key(  # pylint: disable=too-many-return-statements, too-many-branches
        self, key: str
    ) -> bool:
        """Adds text to the field, or moves the cursor."""

        if self.execute_binding(key, ignore_any=True):
            return True

        for name, options in self.keys.items():
            if (
                name.rsplit("_", maxsplit=1)[-1] in ("up", "down")
                and not self.multiline
            ):
                continue

            if key in options:
                return self.handle_action(name)

        if key == keys.TAB:
            if not self.multiline:
                return False

            for _ in range(self.tablength):
                self.handle_key(" ")

            return True

        if key in string.printable and key not in "\x0c\x0b":
            if key == keys.ENTER:
                if not self.multiline:
                    return False

                if len(self._lines) <= self.cursor.row:
                    self._lines.append("")

                line = self._lines[self.cursor.row]
                left, right = line[: self.cursor.col], line[self.cursor.col :]

                self._lines[self.cursor.row] = left
                self._lines.insert(self.cursor.row + 1, right)

                self.move_cursor((1, -self.cursor.col))
                self._styled_cache = None

            else:
                self.insert_text(key)

            if keys.ANY_KEY in self._bindings:
                method, _ = self._bindings[keys.ANY_KEY]
                method(self, key)

            return True

        if key == keys.BACKSPACE:
            if self._selection_length == 1:
                self.delete_back(1)
            else:
                self.delete_back(-self._selection_length)

            self._selection_length = 1
            self._styled_cache = None

            return True

        if len(key) > 1 and not key.startswith("\x1b["):
            for char in key:
                self.handle_key(char)

            return True

        return False

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Allows point-and-click selection."""

        x_offset = event.position[0] - self.pos[0]
        y_offset = event.position[1] - self.pos[1]

        if y_offset == 0:
            x_offset -= len(self.prompt)

            if x_offset < 0:
                return False

        # Set cursor to mouse location
        if event.action is MouseAction.LEFT_CLICK:
            if not y_offset < len(self._lines):
                return False

            line = self._lines[y_offset]

            if y_offset == 0:
                line = self.prompt + line

            self.move_cursor((y_offset, min(len(line), x_offset)), absolute=True)

            self._drag_start = (x_offset, y_offset)
            self._selection_length = 1

            return True

        # Select text using dragging the mouse
        if event.action is MouseAction.LEFT_DRAG and self._drag_start is not None:
            change = x_offset - self._drag_start[0]
            self.update_selection(
                change - self._selection_length + 1, correct_zero_length=False
            )

            return True

        return super().handle_mouse(event)

    def move_cursor(self, new: tuple[int, int], *, absolute: bool = False) -> None:
        """Moves the cursor, then possible re-positions it to a valid location.

        Args:
            new: The new set of (y, x) positions to use.
            absolute: If set, `new` will be interpreted as absolute coordinates,
                instead of being added on top of the current ones.
        """

        if len(self._lines) == 0:
            return

        if absolute:
            new_y, new_x = new
            self.cursor.row = new_y
            self.cursor.col = new_x

        else:
            self.cursor += new

        self.cursor.row = max(0, min(self.cursor.row, len(self._lines) - 1))
        row, col = self.cursor

        line = self._lines[row]
        width = len(line)

        # Going left, possibly upwards
        if col < 0:
            if row <= 0:
                self.cursor.col = 0

            else:
                self.cursor.row -= 1
                line = self._lines[self.cursor.row]
                self.cursor.col = width

        # Going right, possibly downwards
        elif col > width and line != "":
            if len(self._lines) > row + 1:
                self.cursor.row += 1
                self.cursor.col = 0

            line = self._lines[self.cursor.row]

        self.cursor.col = max(0, min(self.cursor.col, width))

    def get_lines(self) -> list[str]:
        """Builds the input field's lines."""

        if not self._cache_is_valid() or self._styled_cache is None:
            self._styled_cache = self._style_and_break_lines()

        lines = self._styled_cache

        row, col = self.cursor

        if len(self._lines) == 0:
            line = " "
        else:
            line = self._lines[row]

        start = col
        cursor_char = " "
        if len(line) > col:
            start = col
            end = col + self._selection_length
            start, end = sorted([start, end])

            try:
                cursor_char = line[start:end]
            except IndexError as error:
                raise ValueError(f"Invalid index in {line!r}: {col}") from error

        style_cursor = (
            self.styles.value if self.selected_index is None else self.styles.cursor
        )

        # TODO: This is horribly hackish, but is the only way to "get around" the
        #       limits of the current scrolling techniques. Should be refactored
        #       once a better solution is available
        if self.parent is not None and self.selected_index is not None:
            offset = 0
            parent = self.parent
            while hasattr(parent, "parent"):
                offset += getattr(parent, "_scroll_offset")

                parent = parent.parent  # type: ignore

            offset_row = -offset + row
            offset_col = start + (len(self.prompt) if row == 0 else 0)

            if offset_col > self.width - 1:
                offset_col -= self.width
                offset_row += 1
                row += 1

                if row >= len(lines):
                    lines.append(self.styles.value(""))

            position = (
                self.pos[0] + offset_col,
                self.pos[1] + offset_row,
            )

            self.positioned_line_buffer.append(
                (position, style_cursor(cursor_char))  # type: ignore
            )

        lines = lines or [""]
        self.height = len(lines)

        return lines
