from __future__ import annotations

from io import StringIO
from typing import Callable

from ..colors import ColorSyntaxError, str_to_color
from ..regex import RE_MACRO
from ..terminal import terminal
from .aliases import apply_default_aliases
from .macros import apply_default_macros
from .parsing import ContextDict, eval_alias, parse


class MarkupLanguage:
    def __init__(
        self, *, default_aliases: bool = True, default_macros: bool = True
    ) -> None:
        self._cache = {}

        self.context = ContextDict.create()
        self._aliases = self.context["aliases"]
        self._macros = self.context["macros"]

        if default_aliases:
            apply_default_aliases(self)

        if default_macros:
            apply_default_macros(self)

    @property
    def aliases(self) -> dict[str, str]:
        return self._aliases.copy()

    @property
    def macros(self) -> dict[str, Callable[[str, ...]]]:
        return self._macros.copy()

    def define(self, name: str, method: Callable[[str, ...], str]) -> None:
        if not name.startswith("!"):
            name = f"!{name}"

        self._macros[name] = method

    def alias(self, name: str, value: str, *, generate_unsetter: bool = True) -> None:
        value = eval_alias(value, self.context)

        def _generate_unsetter() -> str:
            unsetter = ""
            for tag in value.split():
                if tag in self._aliases or tag in self._macros:
                    unsetter += f" /{tag}"
                    continue

                try:
                    color = str_to_color(tag)
                    unsetter += f" /{'bg' if color.background else 'fg'}"

                except ColorSyntaxError:
                    unsetter += f" /{tag}"

            return unsetter.lstrip(" ")

        self._aliases[name] = value

        if generate_unsetter:
            self._aliases[f"/{name}"] = _generate_unsetter()

    def alias_multiple(
        self, *, generate_unsetter: bool = True, **items: dict[str, str]
    ) -> None:
        for name, value in items.items():
            self.alias(name, value, generate_unsetter=generate_unsetter)

    def parse(
        self,
        text: str,
        optimize: bool = True,
        append_reset: bool = True,
    ) -> str:

        key = (text, optimize, append_reset)

        can_cache = key in self._cache
        if "!" in text and RE_MACRO.match(text) is not None:
            can_cache = False

        if can_cache:
            return self._cache[key]

        output = parse(
            text,
            optimize=optimize,
            append_reset=append_reset,
            context=self.context,
        )

        self._cache[key] = output

        return output

    def print(
        self,
        *items,
        sep: str = " ",
        end: str = "\n",
        flush: bool = True,
        file: StringIO = terminal,
    ) -> None:
        buff = []
        for item in items:
            buff.append(self.parse(item))

        file.write(sep.join(buff) + end)

        if flush:
            file.flush()


tim = MarkupLanguage()
