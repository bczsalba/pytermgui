"""The Window class, which is an implementation of `pytermgui.widgets.Container` that
allows for mouse-based moving and resizing."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..widgets import Container
from ..widgets import styles as w_styles, Widget
from ..ansi_interface import MouseEvent, MouseAction
from ..enums import Overflow, SizePolicy, CenteringPolicy

if TYPE_CHECKING:
    from .manager import WindowManager


class Window(Container):  # pylint: disable=too-many-instance-attributes
    """A class representing a window.

    Windows are essentially fancy `pytermgui.widgets.Container`-s. They build on top of them
    to store and display various widgets, while allowing some custom functionality.
    """

    is_bindable = True
    overflow = Overflow.HIDE

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
    """Controls whether the window should be redrawn in the next frame."""

    is_persistent = False
    """Persistent windows will be set noblur automatically, and remain clickable even through
    modals.

    While the library core doesn't do this for various reasons, it also might be useful to disable
    some behaviour (e.g. closing) for persistent windows on an implementation level.
    """

    chars = Container.chars.copy()

    styles = w_styles.StyleManager(
        border=w_styles.FOREGROUND,
        corner=w_styles.FOREGROUND,
        fill="",
        border_focused=w_styles.FOREGROUND,
        corner_focused=w_styles.FOREGROUND,
        border_blurred="238",
        corner_blurred="238",
    )

    def __init__(self, *widgets: Any, **attrs: Any) -> None:
        """Initializes object.

        Args:
            widgets: Widgets to add to this window after initilization.
            attrs: Attributes that are passed to the constructor.
        """

        self._min_width: int | None = None
        self._auto_min_width: int | None = None

        self.styles.border_focused = type(self).styles.border
        self.styles.corner_focused = type(self).styles.corner

        super().__init__(*widgets, **attrs)

        self.has_focus: bool = False

        self.manager: "WindowManager" | None = None

        # -------------------------  position ----- width x height
        self._restore_data: tuple[tuple[int, int], tuple[int, int]] | None = None

        if self.title != "":
            self.set_title(self.title)

        if self.is_persistent:
            self.is_noblur = True

    @property
    def min_width(self) -> int | None:
        """Minimum width of the window.

        If set to none, _auto_min_width will be calculated based on the maximum width of
        inner widgets.

        This is accurate enough for general use, but tends to lean to the safer side,
        i.e. it often overshoots the 'real' minimum width possible.

        If you find this to be the case, **AND** you can ensure that your window will
        not break, you may set this value manually.

        Returns:
            The calculated, or given minimum width of this object.
        """

        return self._min_width or self._auto_min_width

    @min_width.setter
    def min_width(self, new: int | None) -> None:
        """Sets a new minimum width."""

        self._min_width = new

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
        minimum = self.min_width or 0

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

        if len(self._widgets) > 0:
            self._auto_min_width = max(widget.width for widget in self._widgets)
            self._auto_min_width += self.sidelength

        self.height += added.height

        return added

    @classmethod
    def set_focus_styles(
        cls,
        *,
        focused: tuple[w_styles.StyleValue, w_styles.StyleValue],
        blurred: tuple[w_styles.StyleValue, w_styles.StyleValue],
    ) -> None:
        """Sets focused & blurred border & corner styles.

        Args:
            focused: A tuple of border_focused, corner_focused styles.
            blurred: A tuple of border_blurred, corner_blurred styles.
        """

        cls.styles.border_focused, cls.styles.corner_focused = focused
        cls.styles.border_blurred, cls.styles.corner_blurred = blurred

    def focus(self) -> None:
        """Focuses this window."""

        self.has_focus = True

        if not self.is_noblur:
            self.styles.border = self.styles.border_focused
            self.styles.corner = self.styles.corner_focused

    def blur(self) -> None:
        """Blurs (unfocuses) this window."""

        self.has_focus = False
        self.select(None)
        self.handle_mouse(MouseEvent(MouseAction.RELEASE, (0, 0)))

        if not self.is_noblur:
            self.styles.border = self.styles.border_blurred
            self.styles.corner = self.styles.corner_blurred

    def clear_cache(self) -> None:
        """Clears manager compositor's cached blur state."""

        if self.manager is not None:
            self.manager.clear_cache(self)

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

    def center(
        self, where: CenteringPolicy | None = None, store: bool = True
    ) -> Window:
        """Center window"""

        super().center(where, store)
        return self

    def close(self, animate: bool = True) -> None:
        """Instruct window manager to close object"""

        assert self.manager is not None

        self.manager.remove(self, animate=animate)
