"""The module containing all animation-related classes & functions.

This module exports the `animator` name, which is the instance that
is used by the library.
"""

# pylint: disable=too-many-arguments

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Union, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .widgets import Widget
else:
    Widget = Any

AnimationType = Union["Animation", "CustomAnimation"]
AnimationCallback = Callable[[Widget], Union[bool, None]]

__all__ = ["Animator", "Animation", "CustomAnimation", "animator"]


@dataclass
class Animation:
    """A single animation.

    The first callback is called after every step, the second is called
    when the animation finishes.
    """

    target: Widget
    attribute: str
    end: int
    duration: float
    callbacks: tuple[AnimationCallback | None, AnimationCallback | None]
    start: int | None = None

    def __post_init__(self) -> None:
        """Set default values."""

        if self.start is None:
            self.start = getattr(self.target, self.attribute)

        self.start_time = time.time()

    def _get_factor(self) -> float:
        """Calculates the factor of change."""

        return (time.time() - self.start_time) / self.duration

    def step(self) -> bool:
        """Steps the animation forward by elapsed time since instantiation."""

        assert self.start is not None
        if self.duration == 0:
            setattr(self.target, self.attribute, self.end)
            return True

        factor = min(1.0, self._get_factor())
        value = int(self.start + (self.end - self.start) * factor)

        setattr(self.target, self.attribute, int(value))

        step_callback = self.callbacks[0]
        if step_callback is not None:
            step_callback(self.target)

        return value == self.end


@dataclass
class CustomAnimation:
    """A more customizable animation.

    Args:
        step_callback: The function to run on every step call. If this
            function returns True, the animation stops.
    """

    step_callback: Callable[[], bool]

    def step(self) -> bool:
        """Steps ahead in the animation.

        Returns:
            The value self.step_callback returns.
        """

        return self.step_callback()


class Animator:
    """The Animator class

    This class maintains a list of animations (self._animations), stepping
    each of them forward as long as they return False. When they return
    False, the animation is removed from the tracked animations.

    This stepping is done when `step` is called.
    """

    def __init__(self) -> None:
        """Initializes an animator."""

        self._animations: list[AnimationType] = []

    @property
    def is_active(self) -> bool:
        """Determines whether there are any active animations."""

        return len(self._animations) > 0

    def step(self) -> None:
        """Steps the animation forward by the given elapsed time."""

        for animation in self._animations:
            if animation.step():
                self._animations.remove(animation)

                if isinstance(animation, CustomAnimation):
                    continue

                finish_callback = animation.callbacks[1]
                if finish_callback is not None:
                    finish_callback(animation.target)

    def add_custom(self, custom_animation: CustomAnimation) -> None:
        """Adds a custom animation.

        See `CustomAnimation` for more details.
        """

        self._animations.append(custom_animation)

    def animate(
        self,
        widget: Widget,
        attribute: str,
        endpoint: int,
        duration: int,
        startpoint: int | None = None,
        step_callback: AnimationCallback | None = None,
        finish_callback: AnimationCallback | None = None,
    ) -> None:
        """Animates a widget attribute change.

        It instantiates an Animation with the given attributes. This Animation
        is then added to the tracked animations.

        Args:
            widget: The widget to animate.
            attribute: The widget attribute to change.
            startpoint: The starting point of the animation. When set, this
                will be applied to the given widget at animation start. When
                unset, defaults to getattr(widget, attribute).
            endpoint: The ending point of the animation. The animation will end
                once the step function returns the given value.
            duration: The length of time this animation will take. Given in
                milliseconds.
            step_callback: A callable that is called on every step. It is given
                a reference to the widget assigned to the Animation.
            finish_callback: A callable that is called when the Animation.step
                function returns True, e.g. when the animation is finished. It
                is given a reference to the widget assigned to the Animation.
        """

        self._animations.append(
            Animation(
                widget,
                attribute,
                start=startpoint,
                end=endpoint,
                duration=duration / 1000,
                callbacks=(step_callback, finish_callback),
            )
        )


animator = Animator()
"""The global Animator instance used by all of the library."""
