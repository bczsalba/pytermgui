"""The module responsible for creating snazzy color palettes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Generator, Tuple

from .colors import Color
from .fancy_repr import FancyYield
from .markup import MarkupLanguage, tim

SHADE_COUNT = 3
SHADE_FLOOR = 0.4
SHADE_INCREMENT = (1 - SHADE_FLOOR) / SHADE_COUNT

SURFACE = Color.parse("#303030")
SURFACE_ALPHA = 0.2

__all__ = [
    "Palette",
    "triadic",
    "analogous",
    "palette",
]


PaletteGeneratorStrategy = Callable[[Color], Tuple[Color, Color, Color, Color]]
"""Returns 4 colors generated from the base color.

The first color will be used as the primary color. This should _usually_
be the base color, but in some strategies (like analogous) it may not
make sense.

The second and third colors will be the secondary and tertiary colors,
respectively.  The last color will be interpreted as the accent.
"""


def _parse_optional(color: str | None, default: Color) -> Color:
    """Parses optional colors, returns default if None is passed."""

    if color is None:
        return default

    return Color.parse(color, localize=False)


def triadic(base: Color) -> tuple[Color, Color, Color, Color]:
    """Three complementary colors.

    Each color is offset 120 degrees from the previous one on the colorwheel. If
    plotted on the colorwheel, they make up a regular triangle.

    Args:
        base: The color used for derivations.

    ![Triadic strategy](../../assets/triadic.svg)
    """

    return (*base.triadic, base.complement)


def analogous(base: Color) -> tuple[Color, Color, Color, Color]:
    """Colors that sit next to eachother on the colorwheel.

    Args:
        base: The color used for derivations.

    ![Analogous strategy](../../assets/analogous.svg)
    """

    before, _, after = base.analogous

    return base, before, after, base.complement


STRATEGIES = {
    "triadic": triadic,
    "analogous": analogous,
}


@dataclass(repr=False)
class Palette:
    """A harmonious color palette.

    Running `Palette.alias` on a generated palette will create the following color
    aliases:

    !!! cite "Main colors"

        These are the colors used by the majority of the application. Primary should
        make up around 50% percent of an average screen's colors, while secondary and
        tertiary should use the remaining 50% together (25% each).

        Accents should be used sparingly to highlight specific details.

        **Items:** primary, secondary, tertiary, accent

    !!! cite "Semantic colors"

        These colors are all meant to convey some meaning. They shouldn't be used in
        situation where that meaning, e.g. success, isn't clearly related.

        **Items:** success, warning, error

    !!! cite "Neutral colors"

        These are colors meant to be used as a background to the main group. All of them
        are a blend of a default background color and one of the main colors: `surface`
        is generated from `primary`, `surface2` comes from secondary and so on.

        **Items:** surface, surface2, surface3, surface4
    """

    data: dict[str, str]

    @classmethod
    def generate_from(  # pylint: disable=too-many-locals
        cls,
        *,
        primary: str,
        secondary: str | None = None,
        tertiary: str | None = None,
        accent: str | None = None,
        success: str | None = None,
        warning: str | None = None,
        error: str | None = None,
        surface: str | None = None,
        surface2: str | None = None,
        surface3: str | None = None,
        strategy: PaletteGeneratorStrategy = triadic,
    ) -> Palette:
        """Generates a color palette from the given primary color.

        If any other color arguments are passed, they will be parsed as a color
        and used as-is. Otherwise, they will be derived from the primary.

        See the class documentation for info on all arguments.

        Args:
            strategy: A strategy that will be used to derive colors.
        """

        if isinstance(strategy, str):
            old_strat = strategy
            strategy = STRATEGIES.get(strategy)

            if strategy is None:
                raise KeyError(
                    f"Unknown strategy {old_strat!r}. Please choose from"
                    + f" {list(STRATEGIES.keys())}."
                )

        c_primary = Color.parse(primary, localize=False)
        success = success or primary
        warning = warning or primary

        c_primary, *generated = strategy(c_primary)
        c_secondary = _parse_optional(secondary, generated[0])
        c_tertiary = _parse_optional(tertiary, generated[1])
        c_accent = _parse_optional(accent, generated[2])
        c_surface = _parse_optional(surface, SURFACE.blend(c_primary, SURFACE_ALPHA))
        c_surface2 = _parse_optional(
            surface2, SURFACE.blend(c_secondary, SURFACE_ALPHA)
        )
        c_surface3 = _parse_optional(surface3, SURFACE.blend(c_tertiary, SURFACE_ALPHA))
        c_surface4 = _parse_optional(surface3, SURFACE.blend(c_accent, SURFACE_ALPHA))
        c_success = Color.parse(success, localize=False)
        c_warning = Color.parse(warning, localize=False)
        c_error = _parse_optional(error, c_accent)

        base_palette: dict[str, Color] = {
            "primary": c_primary,
            "secondary": c_secondary,
            "tertiary": c_tertiary,
            "accent": c_accent,
            "surface": c_surface,
            "surface2": c_surface2,
            "surface3": c_surface3,
            "surface4": c_surface4,
            "success": c_success,
            "warning": c_warning,
            "error": c_error,
        }

        black = Color.parse("#000000")
        white = Color.parse("#FFFFFF")

        data = {}

        for name, color in base_palette.items():
            for shadenumber in range(-SHADE_COUNT, SHADE_COUNT + 1):
                if shadenumber > 0:
                    shadeindex = f"+{shadenumber}"
                    blend_color = white
                    blend_multiplier = 1

                elif shadenumber == 0:
                    shadeindex = ""

                else:
                    shadeindex = str(shadenumber)
                    blend_color = black
                    blend_multiplier = -1

                if shadenumber == 0:
                    blended = color

                else:
                    blended = color.blend(
                        blend_color, blend_multiplier * SHADE_INCREMENT * shadenumber
                    )

                data[f"{name}{shadeindex}"] = blended

                bg_variant = deepcopy(blended)
                bg_variant.background = True
                data[f"@{name}{shadeindex}"] = bg_variant

        return Palette(
            {
                key: ("@" if color.background else "") + color.hex
                for key, color in data.items()
            }
        )

    def base_keys(self) -> list[str]:
        """Returns the non-background, non-shade alias keys."""

        return [
            key
            for key in self.data
            if not "+" in key and not "-" in key and not key.startswith("@")
        ]

    def alias(self, lang: MarkupLanguage = tim) -> None:
        """Sets up aliases for the given language.

        Note that no unsetters will be generated.

        Args:
            lang: The language to run `alias_multiple` on.
        """

        lang.clear_cache()
        lang.alias_multiple(**self.data, generate_unsetter=False)

    def __fancy_repr__(self) -> Generator[FancyYield, None, None]:
        """Shows off the palette in a compact form."""

        yield f"<{type(self).__name__}"

        for name, value in [
            ("primary", self.data["primary"]),
            ("secondary", self.data["secondary"]),
            ("tertiary", self.data["tertiary"]),
            ("accent", self.data["accent"]),
        ]:
            yield {
                "text": f" {name}: [@{value} #auto]{value}[/]",
                "highlight": False,
            }

        yield ">\n\n"

        length = max(len(key) for key in self.base_keys()) + 2
        for name in self.base_keys():
            line = ""

            for shadenumber in range(-SHADE_COUNT, SHADE_COUNT + 1):
                if shadenumber > 0:
                    shadeindex = f"+{shadenumber}"

                elif shadenumber == 0:
                    line += f"[@{self.data[name]} #auto] {name:^{length}} "
                    continue

                else:
                    shadeindex = str(shadenumber)

                line += f"[@{self.data[name + shadeindex]} #auto]    "

            yield {
                "text": tim.parse(line + "[/]\n"),
                "highlight": False,
            }

    def print(self) -> None:
        """Shows off the palette in an extended form."""

        length = max(len(key) for key in self.base_keys()) + 4
        keys = self.base_keys()

        for name in keys:
            names = []

            for shadenumber in range(-SHADE_COUNT, SHADE_COUNT + 1):
                if shadenumber > 0:
                    shadeindex = f"+{shadenumber}"

                elif shadenumber == 0:
                    shadeindex = ""

                else:
                    shadeindex = str(shadenumber)

                shaded_name = name + shadeindex
                names.append(shaded_name)

            tim.print("".join(f"[@{self.data[name]}]{' ' * length}" for name in names))
            tim.print(
                "".join(
                    f"[@{self.data[name]} bold #auto]"
                    + (name.center(length) if name in keys else " " * length)
                    for name in names
                )
            )
            tim.print(
                "".join(
                    f"[@{self.data[name]} #auto]{self.data[name]:^{length}}"
                    for name in names
                )
            )
            tim.print("".join(f"[@{self.data[name]}]{' ' * length}" for name in names))


palette = Palette.generate_from(
    primary="#7c93d0", success="#93d07b", warning="#d0b97b", error="#d07b92"
)
palette.alias()
