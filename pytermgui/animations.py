"""All animation-related classes & functions.

The biggest exports are `Animation` and its subclasses, as well as `Animator`. A
global instance of `Animator` is also exported, under the `animator` name.

These can be used both within a WindowManager context (where stepping is done
automatically by the `pytermgui.window_manager.Compositor` on every frame, or manually,
by calling `animator.step` with an elapsed time argument.

You can register animations to the Animator using either its `schedule` method, with
an already constructed `Animation` subclass, or either `Animator.animate_attr` or
`Animator.animate_float` for an in-place construction of the animation instance.
"""

# pylint: disable=too-many-arguments, too-many-instance-attributes

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .widgets import Widget
else:
    Widget = Any

__all__ = ["Animator", "FloatAnimation", "AttrAnimation", "animator", "is_animated"]


def _add_flag(target: object, attribute: str) -> None:
    """Adds attribute to `target.__ptg_animated__`.

    If the list doesn't exist, it is created with the attribute.
    """

    if not hasattr(target, "__ptg_animated__"):
        setattr(target, "__ptg_animated__", [])

    animated = getattr(target, "__ptg_animated__")
    animated.append(attribute)


def _remove_flag(target: object, attribute: str) -> None:
    """Removes attribute from `target.__ptg_animated__`.

    If the animated list is empty, it is `del`-d from the object.
    """

    animated = getattr(target, "__ptg_animated__", None)
    if animated is None:
        raise ValueError(f"Object {target!r} seems to not be animated.")

    animated.remove(attribute)
    if len(animated) == 0:
        del target.__dict__["__ptg_animated__"]


def is_animated(target: object, attribute: str) -> bool:
    """Determines whether the given object.attribute is animated.

    This looks for `__ptg_animated__`, and whether it contains the given attribute.
    """

    if not hasattr(target, "__ptg_animated__"):
        return False

    animated = getattr(target, "__ptg_animated__")

    return attribute in animated


class Direction(Enum):
    """Animation directions."""

    FORWARD = 1
    BACKWARD = -1


@dataclass
class Animation:
    """The baseclass for all animations."""

    duration: int
    direction: Direction
    loop: bool

    on_step: Callable[[Animation], bool] | None
    on_finish: Callable[[Animation], None] | None

    state: float
    _remaining: float

    def __post_init__(self) -> None:
        self.state = 0.0 if self.direction is Direction.FORWARD else 1.0
        self._remaining = self.duration
        self._is_paused = False

    def _update_state(self, elapsed: float) -> bool:
        """Updates the internal float state of the animation.

        Args:
            elapsed: The time elapsed since last update.

        Returns:
            True if the animation deems itself complete, False otherwise.
        """

        if self._is_paused:
            return False

        self._remaining -= elapsed * 1000

        self.state = (self.duration - self._remaining) / self.duration

        if self.direction is Direction.BACKWARD:
            self.state = 1 - self.state

        self.state = min(self.state, 1.0)

        if not 0.0 <= self.state < 1.0:
            if not self.loop:
                return True

            self._remaining = self.duration
            self.direction = Direction(self.direction.value * -1)

        return False

    def pause(self, setting: bool = True) -> None:
        """Pauses the animation."""

        self._is_paused = setting

    def resume(self) -> None:
        """Resumes the animation."""

        self.pause(False)

    def step(self, elapsed: float) -> bool:
        """Updates animation state.

        This should call `_update_state`, passing in the elapsed value. That call
        will update the `state` attribute, which can then be used to animate things.

        Args:
            elapsed: The time elapsed since last update.
        """

        state_finished = self._update_state(elapsed)

        step_finished = False
        if self.on_step is not None:
            step_finished = self.on_step(self)

        return state_finished or step_finished

    def finish(self) -> None:
        """Finishes and cleans up after the animation.

        Called by `Animator` after `on_step` returns True. Should call `on_finish` if it
        is not None.
        """

        if self.on_finish is not None:
            self.on_finish(self)


@dataclass
class FloatAnimation(Animation):
    """Transitions a floating point number from 0.0 to 1.0.

    Note that this is just a wrapper over the base class, and provides no extra
    functionality.
    """

    duration: int

    on_step: Callable[[Animation], bool] | None = None
    on_finish: Callable[[Animation], None] | None = None

    direction: Direction = Direction.FORWARD
    loop: bool = False

    state: float = field(init=False)
    _remaining: int = field(init=False)


@dataclass
class AttrAnimation(Animation):
    """Animates an attribute going from one value to another."""

    target: object = None
    attr: str = ""
    value_type: type = int
    end: int | float = 0
    start: int | float | None = None

    on_step: Callable[[Animation], bool] | None = None
    on_finish: Callable[[Animation], None] | None = None

    direction: Direction = Direction.FORWARD
    loop: bool = False

    state: float = field(init=False)
    _remaining: int = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.start is None:
            self.start = getattr(self.target, self.attr)

        if self.end < self.start:
            self.start, self.end = self.end, self.start
            self.direction = Direction.BACKWARD

        self.end -= self.start

        _add_flag(self.target, self.attr)

    def step(self, elapsed: float) -> bool:
        """Steps forward in the attribute animation."""

        state_finished = self._update_state(elapsed)

        step_finished = False

        assert self.start is not None

        updated = self.start + (self.end * self.state)
        setattr(self.target, self.attr, self.value_type(updated))

        if self.on_step is not None:
            step_finished = self.on_step(self)

        if step_finished or state_finished:
            return True

        return False

    def finish(self) -> None:
        """Deletes `__ptg_animated__` flag, calls `on_finish`."""

        _remove_flag(self.target, self.attr)
        super().finish()


class Animator:
    """The Animator class

    This class maintains a list of animations (self._animations), stepping
    each of them forward as long as they return False. When they return
    False, the animation is removed from the tracked animations.

    This stepping is done when `step` is called.
    """

    def __init__(self) -> None:
        """Initializes an animator."""

        self._animations: list[Animation] = []

    def __contains__(self, item: object) -> bool:
        """Returns whether the item is inside _animations."""

        return item in self._animations

    @property
    def is_active(self) -> bool:
        """Determines whether there are any active animations."""

        return len(self._animations) > 0

    def step(self, elapsed: float) -> None:
        """Steps the animation forward by the given elapsed time."""

        for animation in self._animations.copy():
            if animation.step(elapsed):
                self._animations.remove(animation)
                animation.finish()

    def schedule(self, animation: Animation) -> None:
        """Starts an animation on the next step."""

        self._animations.append(animation)

    def animate_attr(self, **animation_args: Any) -> AttrAnimation:
        """Creates and schedules an AttrAnimation.

        All arguments are passed to the `AttrAnimation` constructor. `direction`, if
        given as an integer, will be converted to a `Direction` before being passed.

        Returns:
            The created animation.
        """

        if "direction" in animation_args:
            animation_args["direction"] = Direction(animation_args["direction"])

        anim = AttrAnimation(**animation_args)
        self.schedule(anim)

        return anim

    def animate_float(self, **animation_args: Any) -> FloatAnimation:
        """Creates and schedules an Animation.

        All arguments are passed to the `Animation` constructor. `direction`, if
        given as an integer, will be converted to a `Direction` before being passed.

        Returns:
            The created animation.
        """

        if "direction" in animation_args:
            animation_args["direction"] = Direction(animation_args["direction"])

        anim = FloatAnimation(**animation_args)
        self.schedule(anim)

        return anim


animator = Animator()
"""The global Animator instance used by all of the library."""
