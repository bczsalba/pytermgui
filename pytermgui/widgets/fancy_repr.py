"""A widget to wrap objects supporting the `fancy_repr` protocol."""

from __future__ import annotations

from typing import Any

from ..fancy_repr import SupportsFancyRepr, build_fancy_repr
from ..markup import tim
from .base import Widget

__all__ = ["FancyReprWidget"]


class FancyReprWidget(Widget):
    """A widget that wraps objects supporting the `fancy_repr` protocol."""

    def __init__(
        self, target: SupportsFancyRepr, starts_at: int = 0, **attrs: Any
    ) -> None:
        self.target = target
        self.starts_at = starts_at

        super().__init__(**attrs)

    def get_lines(self) -> list[str]:
        """Builds fancy repr of target and returns it."""

        start = self.starts_at
        lines = [
            tim.parse(line)
            for line in build_fancy_repr(self.target).splitlines()[start:]
        ]

        self.width = max(len(line) for line in lines)
        self.height = len(lines)

        return lines
