"""Layouts for the WindowManager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union

from ..regex import real_length
from ..term import Terminal, get_terminal
from ..widgets import Widget

DimensionSource = Union["Dimension", int, float, None]


class Dimension:
    """The base class for layout dimensions.

    Each dimension has a `value` property. This returns an integer,
    and is essentially the *meaning* of the object.
    """

    _value: int

    @property
    def value(self) -> int:
        """Returns the value of the object.

        Override this for custom behaviour."""

        return self._value

    @value.setter
    def value(self, new: int) -> None:
        """Sets a new value."""

        self._value = new

    def __repr__(self) -> str:
        """Returns `{typename}(value={value})`.

        We use this over the dataclasses one as that used `_value`, and it's
        a bit ugly.
        """

        return f"{type(self).__name__}(value={self.value})"


@dataclass(repr=False, frozen=True)
class Static(Dimension):
    """A static dimension.

    This dimension is immutable, and the Layout will always leave it unchanged.
    """

    _value: int = 0


@dataclass(repr=False)
class Relative(Dimension):
    """A relative dimension.

    This dimension has a scale attribute and bound method. Every time  the `value`
    is queried, `int(self.bound() * self.scale)` is returned.

    When instantiated through `Layout.add_slot`, `bound` will default to either
    the parent's width or height, depending on which attribute it is applied to.
    """

    _value = 0
    scale: float
    bound: Callable[[], int]

    @property
    def value(self) -> int:
        """Calculates the new value for the dimension."""

        return int(self.bound() * self.scale)

    @value.setter
    def value(self, new: int) -> None:
        """Disallows setting the value.

        We can't inherit and then override a set-get property with a get one, so this
        kind of patches that issue up.
        """

        raise TypeError

    def __repr__(self) -> str:
        scale = self.scale
        bound = self.bound

        original = super().__repr__()
        return original[:-1] + f", {scale=}, {bound=}" + original[-1]


@dataclass
class Auto(Dimension):
    """An automatically calculated dimension.

    The value of this dimension is overwritten on `Layout.apply`.

    Generally, the way calculations are done is by looking at the available
    size of the layout by subtracting the sum of all the non-auto dimensions
    from the parent's width or height, and dividing it by the number of
    Auto-type dimensions in the current context.

    An additional offset is applied to the first dimension (left-most or top-most)
    of the context when the division has a remainder.
    """

    _value = 0

    def __repr__(self) -> str:
        return f"{type(self).__name__}(value={self.value})"


@dataclass
class Slot:
    """A slot within a layout.

    A slot has a name, width & height, as well as some content. It's `apply` method
    can be called to apply the slot's position & dimensions to its content.
    """

    name: str
    width: Dimension
    height: Dimension

    inner_pos: tuple[int, int] = (0, 0)
    content: Widget | None = None

    _restore_data: tuple[int, int, tuple[int, int]] | None = None

    def apply(self, position: tuple[int, int], origin: tuple[int, int]) -> None:
        """Applies the given position & dimension to the content.

        Args:
            position: The position that this object resides in. Set as its content's `pos`.
        """

        if self.content is None or self.width is None or self.height is None:
            return

        if self._restore_data is None:
            self._restore_data = (
                self.content.width,
                self.content.height,
                self.content.pos,
            )

        self.content.height = self.height.value
        self.content.width = self.width.value

        self.inner_pos = position
        self.content.pos = origin[0] + position[0], origin[1] + position[1]

    def detach_content(self) -> None:
        """Detaches content & restores its original state."""

        content = self.content
        if content is None:
            raise AttributeError(f"No content to detach in {self!r}.")

        assert self._restore_data is not None

        content.width, content.height, content.pos = self._restore_data

        self.content = None
        self._restore_data = None


ROW_BREAK = Slot("Row Break", Static(0), Static(0))
"""When encountered in `Layout.build_rows`, a new row will be started at the next element."""


class Layout:
    """Defines a layout of Widgets, used by WindowManager.

    Internally, it keeps track of a list of `Slot`. This list is then turned into a list
    of rows, all containing slots. This is done either when the current row has run out
    of the parent's width, or `ROW_BREAK` is encountered.
    """

    name: str

    def __init__(self, parent: Widget | None = None, name: str = "Layout") -> None:
        self.name = name
        self.slots: list[Slot] = []

        self._parent = parent

    def __len__(self) -> int:
        """Gets the slot count of this layout."""

        return len(self.slots)

    @property
    def parent(self) -> Widget | Terminal:
        """Gets and sets the parent of the layout.

        The parent is used to gather information on widths & heights.
        """

        return self._parent or get_terminal()

    @parent.setter
    def parent(self, new: Widget | Terminal | None) -> None:
        """Sets the parent of the layout."""

        self._parent = new

    @property
    def parent_width(self) -> int:
        """Gets the parent's usable width."""

        return self.parent.frame_content_size[0]

    @property
    def parent_height(self) -> int:
        """Gets the parent's usable height."""

        return self.parent.frame_content_size[1]

    def _to_rows(self) -> list[list[Slot]]:
        """Breaks `self.slots` into a list of list of slots.

        The parent's remaining width is kept track of, and when a slot doesn't have enough
        space left it is pushed to a new row. Additionally, `ROW_BREAK` will force a new
        row to be created, starting with the next slot.
        """

        rows: list[list[Slot]] = []
        available = self.parent.width

        row: list[Slot] = []
        for slot in self.slots:
            if available <= 0 or slot is ROW_BREAK:
                rows.append(row)

                row = []
                available = self.parent.width - slot.width.value

            if slot is ROW_BREAK:
                continue

            available -= slot.width.value
            row.append(slot)

        if len(row) > 0:
            rows.append(row)

        return rows

    def build_rows(self) -> list[list[Slot]]:
        """Builds a list of slot rows, breaking them & applying automatic dimensions.

        Returns:
            A list[list[Slot]], aka. a list of slot-rows.
        """

        def _get_height(row: list[Slot]) -> int:
            defined = list(filter(lambda slot: not isinstance(slot.height, Auto), row))

            if len(defined) > 0:
                return max(slot.height.value for slot in defined)

            return 0

        def _calculate_widths(row: list[Slot]) -> tuple[int, int]:
            defined: list[Slot] = list(
                filter(lambda slt: not isinstance(slt.width, Auto), row)
            )
            undefined = list(filter(lambda slt: slt not in defined, row))

            available = self.parent_width - sum(slot.width.value for slot in defined)

            return divmod(available, len(undefined) or 1)

        def _calculate_heights(rows: list[list[Slot]]) -> tuple[int, int]:
            heights = [_get_height(row) for row in rows]

            occupied = sum(heights)
            return heights, divmod(self.parent_height - occupied, heights.count(0) or 1)

        rows = self._to_rows()

        heights, (auto_height, extra_height) = _calculate_heights(rows)
        extra_height_per_row = extra_height // (len(rows) or 1)

        for row, height in zip(rows, heights):
            if len(row) == 0:
                continue

            height = height or auto_height

            auto_width, extra_width = _calculate_widths(row)

            extra_width_per_slot = extra_width // len(row)

            for slot in row:
                width = auto_width if isinstance(slot.width, Auto) else slot.width.value

                if isinstance(slot.height, Auto):
                    slot.height.value = max(height + extra_height_per_row, 1)
                    extra_height_per_row = 0

                if isinstance(slot.width, Auto):
                    slot.width.value = width + extra_width_per_slot
                    extra_width -= extra_width_per_slot

        return rows

    def add_slot(
        self,
        name: str = "Slot",
        *,
        slot: Slot | None = None,
        width: DimensionSource = None,
        height: DimensionSource = None,
        index: int = -1,
    ) -> Slot:
        """Adds a new slot to the layout.

        Args:
            name: The name of the slot. Used for display purposes.
            slot: An already instantiated `Slot` instance. If this is given,
                the additional width & height arguments will be ignored.
            width: The width for the new slot. See below for special types.
            height: The height for the new slot. See below for special types.
            index: The index to add the new slot to.

        Returns:
            The just-added slot.

        When defining dimensions, either width or height, some special value
        types can be given:
        - `Dimension`: Passed directly to the new slot.
        - `None`: An `Auto` dimension is created with no value.
        - `int`: A `Static` dimension is created with the given value.
        - `float`: A `Relative` dimension is created with the given value as its
            scale. Its `bound` attribute will default to the relevant part of the
            parent's size.
        """

        if slot is None:
            if width is None:
                width = Auto()

            elif isinstance(width, int):
                width = Static(width)

            elif isinstance(width, float):
                width = Relative(width, bound=lambda: self.parent.width)

            if height is None:
                height = Auto()

            elif isinstance(height, int):
                height = Static(height)

            elif isinstance(height, float):
                height = Relative(height, bound=lambda: self.parent.height)

            slot = Slot(name, width=width, height=height)

        if index == -1:
            self.slots.append(slot)
            return slot

        self.slots.insert(index, slot)

        return slot

    def add_break(self, *, index: int = -1) -> None:
        """Adds `ROW_BREAK` to the given index.

        This special slot is ignored for all intents and purposes, other than when
        breaking the slots into rows. In that context, when encountered, the current
        row is deemed completed, and the next slot will go into a new row list.
        """

        self.add_slot(slot=ROW_BREAK, index=index)

    def assign(self, widget: Widget, *, index: int = -1) -> None:
        """Assigns a widget to the slot at the specified index.

        Args:
            widget: The widget to assign.
            index: The target slot's index.
            apply: If set, `apply` will be called once the widget has been assigned.
        """

        slots = [slot for slot in self.slots if slot is not ROW_BREAK]
        if index > len(slots) - 1:
            return

        slot = slots[index]

        slot.content = widget

    def apply(self, origin: tuple[int, int]) -> None:
        """Applies the layout to each slot."""

        position = [0, 0]

        for row in self.build_rows():
            if len(row) == 0:
                continue

            position[0] = 0

            for slot in row:
                slot.apply(tuple(position), origin=origin)

                position[0] += slot.width.value

            position[1] += max(slot.height.value for slot in row)

    def build_lines(self) -> list[str]:
        """Builds widget-displayable lines of this layout & its widgets."""

        lines = []

        for row in self.build_rows():
            row_lines = []

            for slot in row:
                if slot.content is None:
                    continue

                widget_lines = slot.content.get_lines()

                difference = len(widget_lines) - len(row_lines)
                if difference > 0:
                    row_lines.extend([""] * difference)

                x_pos = slot.inner_pos[0]

                for i, (base, new) in enumerate(zip(row_lines, widget_lines)):
                    line_len_diff = x_pos - real_length(base)

                    if line_len_diff < 0:
                        continue

                    if line_len_diff > 0:
                        base += " " * line_len_diff

                    row_lines[i] = base + new

            lines.extend(row_lines)

        return lines

    def __getattr__(self, attr: str) -> Slot:
        """Gets a slot by its (slugified) name."""

        def _snakeify(name: str) -> str:
            return name.lower().replace(" ", "_")

        for slot in self.slots:
            if _snakeify(slot.name) == attr:
                return slot

        raise AttributeError(f"Slot with name {attr!r} could not be found.")
