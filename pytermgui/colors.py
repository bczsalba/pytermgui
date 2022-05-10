"""The module containing all of the color-centric features of this library.

This module provides a base class, `Color`, and a bunch of abstractions over it.

Shoutout to: https://stackoverflow.com/a/33206814, one of the best StackOverflow
answers I've ever bumped into.
"""

# pylint: disable=too-many-instance-attributes


from __future__ import annotations

import re
import sys
from math import sqrt  # pylint: disable=no-name-in-module
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Type, Literal
from functools import lru_cache, cached_property

from .input import getch
from .exceptions import ColorSyntaxError
from .terminal import terminal, ColorSystem
from .ansi_interface import reset as reset_style

if TYPE_CHECKING:
    # This cyclic won't be relevant while type checking.
    from .parser import StyledText  # pylint: disable=cyclic-import

__all__ = [
    "COLOR_TABLE",
    "XTERM_NAMED_COLORS",
    "NAMED_COLORS",
    "clear_color_cache",
    "foreground",
    "background",
    "str_to_color",
    "Color",
    "IndexedColor",
    "RGBColor",
    "HEXColor",
]


RE_256 = re.compile(r"^([\d]{1,3})$")
RE_HEX = re.compile(r"(?:#)?([0-9a-fA-F]{6})")
RE_RGB = re.compile(r"(\d{1,3};\d{1,3};\d{1,3})")

RE_PALETTE_REPLY = re.compile(
    r"\x1b]((?:10)|(?:11));rgb:([0-9a-f]{4})\/([0-9a-f]{4})\/([0-9a-f]{4})\x1b\\"
)

# Adapted from https://gist.github.com/MicahElliott/719710
# TODO: Maybe this could be generated dynamically?
#       See https://superuser.com/a/905280
COLOR_TABLE = [
    (0, 0, 0),
    (170, 0, 0),
    (0, 170, 0),
    (170, 85, 0),
    (0, 0, 170),
    (170, 0, 170),
    (0, 170, 170),
    (170, 170, 170),
    (85, 85, 85),
    (255, 85, 85),
    (85, 255, 85),
    (255, 255, 85),
    (85, 85, 255),
    (255, 85, 255),
    (85, 255, 255),
    (255, 255, 255),
    (0, 0, 0),
    (0, 0, 95),
    (0, 0, 135),
    (0, 0, 175),
    (0, 0, 215),
    (0, 0, 255),
    (0, 95, 0),
    (0, 95, 95),
    (0, 95, 135),
    (0, 95, 175),
    (0, 95, 215),
    (0, 95, 255),
    (0, 135, 0),
    (0, 135, 95),
    (0, 135, 135),
    (0, 135, 175),
    (0, 135, 215),
    (0, 135, 255),
    (0, 175, 0),
    (0, 175, 95),
    (0, 175, 135),
    (0, 175, 175),
    (0, 175, 215),
    (0, 175, 255),
    (0, 215, 0),
    (0, 215, 95),
    (0, 215, 135),
    (0, 215, 175),
    (0, 215, 215),
    (0, 215, 255),
    (0, 255, 0),
    (0, 255, 95),
    (0, 255, 135),
    (0, 255, 175),
    (0, 255, 215),
    (0, 255, 255),
    (95, 0, 0),
    (95, 0, 95),
    (95, 0, 135),
    (95, 0, 175),
    (95, 0, 215),
    (95, 0, 255),
    (95, 95, 0),
    (95, 95, 95),
    (95, 95, 135),
    (95, 95, 175),
    (95, 95, 215),
    (95, 95, 255),
    (95, 135, 0),
    (95, 135, 95),
    (95, 135, 135),
    (95, 135, 175),
    (95, 135, 215),
    (95, 135, 255),
    (95, 175, 0),
    (95, 175, 95),
    (95, 175, 135),
    (95, 175, 175),
    (95, 175, 215),
    (95, 175, 255),
    (95, 215, 0),
    (95, 215, 95),
    (95, 215, 135),
    (95, 215, 175),
    (95, 215, 215),
    (95, 215, 255),
    (95, 255, 0),
    (95, 255, 95),
    (95, 255, 135),
    (95, 255, 175),
    (95, 255, 215),
    (95, 255, 255),
    (135, 0, 0),
    (135, 0, 95),
    (135, 0, 135),
    (135, 0, 175),
    (135, 0, 215),
    (135, 0, 255),
    (135, 95, 0),
    (135, 95, 95),
    (135, 95, 135),
    (135, 95, 175),
    (135, 95, 215),
    (135, 95, 255),
    (135, 135, 0),
    (135, 135, 95),
    (135, 135, 135),
    (135, 135, 175),
    (135, 135, 215),
    (135, 135, 255),
    (135, 175, 0),
    (135, 175, 95),
    (135, 175, 135),
    (135, 175, 175),
    (135, 175, 215),
    (135, 175, 255),
    (135, 215, 0),
    (135, 215, 95),
    (135, 215, 135),
    (135, 215, 175),
    (135, 215, 215),
    (135, 215, 255),
    (135, 255, 0),
    (135, 255, 95),
    (135, 255, 135),
    (135, 255, 175),
    (135, 255, 215),
    (135, 255, 255),
    (175, 0, 0),
    (175, 0, 95),
    (175, 0, 135),
    (175, 0, 175),
    (175, 0, 215),
    (175, 0, 255),
    (175, 95, 0),
    (175, 95, 95),
    (175, 95, 135),
    (175, 95, 175),
    (175, 95, 215),
    (175, 95, 255),
    (175, 135, 0),
    (175, 135, 95),
    (175, 135, 135),
    (175, 135, 175),
    (175, 135, 215),
    (175, 135, 255),
    (175, 175, 0),
    (175, 175, 95),
    (175, 175, 135),
    (175, 175, 175),
    (175, 175, 215),
    (175, 175, 255),
    (175, 215, 0),
    (175, 215, 95),
    (175, 215, 135),
    (175, 215, 175),
    (175, 215, 215),
    (175, 215, 255),
    (175, 255, 0),
    (175, 255, 95),
    (175, 255, 135),
    (175, 255, 175),
    (175, 255, 215),
    (175, 255, 255),
    (215, 0, 0),
    (215, 0, 95),
    (215, 0, 135),
    (215, 0, 175),
    (215, 0, 215),
    (215, 0, 255),
    (215, 95, 0),
    (215, 95, 95),
    (215, 95, 135),
    (215, 95, 175),
    (215, 95, 215),
    (215, 95, 255),
    (215, 135, 0),
    (215, 135, 95),
    (215, 135, 135),
    (215, 135, 175),
    (215, 135, 215),
    (215, 135, 255),
    (215, 175, 0),
    (215, 175, 95),
    (215, 175, 135),
    (215, 175, 175),
    (215, 175, 215),
    (215, 175, 255),
    (215, 215, 0),
    (215, 215, 95),
    (215, 215, 135),
    (215, 215, 175),
    (215, 215, 215),
    (215, 215, 255),
    (215, 255, 0),
    (215, 255, 95),
    (215, 255, 135),
    (215, 255, 175),
    (215, 255, 215),
    (215, 255, 255),
    (255, 0, 0),
    (255, 0, 95),
    (255, 0, 135),
    (255, 0, 175),
    (255, 0, 215),
    (255, 0, 255),
    (255, 95, 0),
    (255, 95, 95),
    (255, 95, 135),
    (255, 95, 175),
    (255, 95, 215),
    (255, 95, 255),
    (255, 135, 0),
    (255, 135, 95),
    (255, 135, 135),
    (255, 135, 175),
    (255, 135, 215),
    (255, 135, 255),
    (255, 175, 0),
    (255, 175, 95),
    (255, 175, 135),
    (255, 175, 175),
    (255, 175, 215),
    (255, 175, 255),
    (255, 215, 0),
    (255, 215, 95),
    (255, 215, 135),
    (255, 215, 175),
    (255, 215, 215),
    (255, 215, 255),
    (255, 255, 0),
    (255, 255, 95),
    (255, 255, 135),
    (255, 255, 175),
    (255, 255, 215),
    (255, 255, 255),
    (8, 8, 8),
    (18, 18, 18),
    (28, 28, 28),
    (38, 38, 38),
    (48, 48, 48),
    (58, 58, 58),
    (68, 68, 68),
    (78, 78, 78),
    (88, 88, 88),
    (98, 98, 98),
    (108, 108, 108),
    (118, 118, 118),
    (128, 128, 128),
    (138, 138, 138),
    (148, 148, 148),
    (158, 158, 158),
    (168, 168, 168),
    (178, 178, 178),
    (188, 188, 188),
    (198, 198, 198),
    (208, 208, 208),
    (218, 218, 218),
    (228, 228, 228),
    (238, 238, 238),
]

XTERM_NAMED_COLORS = {
    0: "black",
    1: "red",
    2: "green",
    3: "yellow",
    4: "blue",
    5: "magenta",
    6: "cyan",
    7: "white",
    8: "bright-black",
    9: "bright-red",
    10: "bright-green",
    11: "bright-yellow",
    12: "bright-blue",
    14: "bright-magenta",
    15: "bright-cyan",
    16: "bright-white",
}

NAMED_COLORS = {**{color: str(index) for index, color in XTERM_NAMED_COLORS.items()}}

_COLOR_CACHE: dict[str, Color] = {}
_COLOR_MATCH_CACHE: dict[tuple[float, float, float], Color] = {}


def clear_color_cache() -> None:
    """Clears `_COLOR_CACHE` and `_COLOR_MATCH_CACHE`."""

    _COLOR_CACHE.clear()
    _COLOR_MATCH_CACHE.clear()


def _get_palette_color(color: Literal["10", "11"]) -> Color:
    """Gets either the foreground or background color of the current emulator.

    Args:
        color: The value used for `Ps` in the query. See https://unix.stackexchange.com/a/172674.
    """

    defaults = {
        "10": RGBColor.from_rgb((222, 222, 222)),
        "11": RGBColor.from_rgb((20, 20, 20)),
    }

    if not terminal.isatty():
        return defaults[color]

    sys.stdout.write(f"\x1b]{color};?\007")
    sys.stdout.flush()

    reply = getch()

    match = RE_PALETTE_REPLY.match(reply)
    if match is None:
        return defaults[color]

    _, red, green, blue = match.groups()

    rgb: list[int] = []
    for part in (red, green, blue):
        rgb.append(int(part[:2], base=16))

    palette_color = RGBColor.from_rgb(tuple(rgb))  # type: ignore
    palette_color.background = color == "11"

    return palette_color


@dataclass
class Color:
    """A terminal color.

    Args:
        value: The data contained within this color.
        background: Whether this color will represent a color.
    """

    value: str
    background: bool = False

    system: ColorSystem = field(init=False)

    default_foreground: Color | None = field(default=None, repr=False)
    default_background: Color | None = field(default=None, repr=False)

    _luminance: float | None = field(init=False, default=None, repr=False)
    _brightness: float | None = field(init=False, default=None, repr=False)
    _rgb: tuple[int, int, int] | None = field(init=False, default=None, repr=False)

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int]) -> Color:
        """Creates a color from the given RGB, within terminal's colorsystem.

        Args:
            rgb: The RGB value to base the new color off of.
        """

        raise NotImplementedError

    @property
    def sequence(self) -> str:
        """Returns the ANSI sequence representation of the color."""

        raise NotImplementedError

    @cached_property
    def rgb(self) -> tuple[int, int, int]:
        """Returns this color as a tuple of (red, green, blue) values."""

        if self._rgb is None:
            raise NotImplementedError

        return self._rgb

    @cached_property
    def hex(self) -> str:
        """Returns CSS-like HEX representation of this color."""

        buff = "#"
        for color in self.rgb:
            buff += f"{format(color, 'x'):0>2}"

        return buff

    @classmethod
    def get_default_foreground(cls) -> Color:
        """Gets the terminal emulator's default foreground color."""

        if cls.default_foreground is not None:
            return cls.default_foreground

        return _get_palette_color("10")

    @classmethod
    def get_default_background(cls) -> Color:
        """Gets the terminal emulator's default foreground color."""

        if cls.default_background is not None:
            return cls.default_background

        return _get_palette_color("11")

    @property
    def name(self) -> str:
        """Returns the reverse-parseable name of this color."""

        return ("@" if self.background else "") + self.value

    @property
    def luminance(self) -> float:
        """Returns this color's perceived luminance (brightness).

        From https://stackoverflow.com/a/596243
        """

        # Don't do expensive calculations over and over
        if self._luminance is not None:
            return self._luminance

        def _linearize(color: float) -> float:
            """Converts sRGB color to linear value."""

            if color <= 0.04045:
                return color / 12.92

            return ((color + 0.055) / 1.055) ** 2.4

        red, green, blue = float(self.rgb[0]), float(self.rgb[1]), float(self.rgb[2])

        red /= 255
        green /= 255
        blue /= 255

        red = _linearize(red)
        blue = _linearize(blue)
        green = _linearize(green)

        self._luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue

        return self._luminance

    @property
    def brightness(self) -> float:
        """Returns the perceived "brightness" of a color.

        From https://stackoverflow.com/a/56678483
        """

        # Don't do expensive calculations over and over
        if self._brightness is not None:
            return self._brightness

        if self.luminance <= (216 / 24389):
            brightness = self.luminance * (24389 / 27)

        else:
            brightness = self.luminance ** (1 / 3) * 116 - 16

        self._brightness = brightness / 100
        return self._brightness

    def __call__(self, text: str, reset: bool = True) -> StyledText:
        """Colors the given string, returning a `pytermgui.parser.StyledText`."""

        # We import this here as toplevel would cause circular imports, and it won't
        # be used until this method is called anyways.
        from .parser import StyledText  # pylint: disable=import-outside-toplevel

        buff = self.sequence + text
        if reset:
            buff += reset_style()

        return StyledText(buff)

    def get_localized(self) -> Color:
        """Creates a terminal-capability local Color instance.

        This method essentially allows for graceful degradation of colors in the
        terminal.
        """

        system = terminal.colorsystem
        if self.system <= system:
            return self

        colortype = SYSTEM_TO_TYPE[system]

        local = colortype.from_rgb(self.rgb)
        local.background = self.background

        return local


@dataclass(repr=False)
class IndexedColor(Color):
    """A color representing an index into the xterm-256 color palette."""

    system = ColorSystem.EIGHT_BIT

    def __post_init__(self) -> None:
        """Ensures data validity."""

        if not self.value.isdigit():
            raise ValueError(
                f"IndexedColor value has to be numerical, got {self.value!r}."
            )

        if not 0 <= int(self.value) < 256:
            raise ValueError(
                f"IndexedColor value has to fit in range 0-255, got {self.value!r}."
            )

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int]) -> IndexedColor:
        """Constructs an `IndexedColor` from the closest matching option."""

        if rgb in _COLOR_MATCH_CACHE:
            color = _COLOR_MATCH_CACHE[rgb]

            assert isinstance(color, IndexedColor)
            return color

        if terminal.colorsystem == ColorSystem.STANDARD:
            return StandardColor.from_rgb(rgb)

        # Normalize the color values
        red, green, blue = (x / 255 for x in rgb)

        # Calculate the eight-bit color index
        color_num = 16
        color_num += 36 * round(red * 5.0)
        color_num += 6 * round(green * 5.0)
        color_num += round(blue * 5.0)

        color = cls(str(color_num))
        _COLOR_MATCH_CACHE[rgb] = color

        return color

    @property
    def sequence(self) -> str:
        r"""Returns an ANSI sequence representing this color."""

        index = int(self.value)

        return "\x1b[" + ("48" if self.background else "38") + f";5;{index}m"

    @cached_property
    def rgb(self) -> tuple[int, int, int]:
        """Returns an RGB representation of this color."""

        if self._rgb is not None:
            return self._rgb

        index = int(self.value)
        rgb = COLOR_TABLE[index]

        return (rgb[0], rgb[1], rgb[2])


class StandardColor(IndexedColor):
    """A color in the xterm-16 palette."""

    system = ColorSystem.STANDARD

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int]) -> StandardColor:
        """Creates a color with the closest-matching xterm index, based on rgb.

        Args:
            rgb: The target color.
        """

        if rgb in _COLOR_MATCH_CACHE:
            color = _COLOR_MATCH_CACHE[rgb]

            if color.system is ColorSystem.STANDARD:
                assert isinstance(color, StandardColor)
                return color

        # Find the least-different color in the table
        index = min(range(16), key=lambda i: _get_color_difference(rgb, COLOR_TABLE[i]))
        color = cls(str(index))

        _COLOR_MATCH_CACHE[rgb] = color

        return color

    @property
    def sequence(self) -> str:
        r"""Returns an ANSI sequence representing this color."""

        index = int(self.value)

        if index <= 7:
            index += 30

        else:
            index = index + 82

        if self.background:
            index += 10

        return f"\x1b[{index}m"


class GreyscaleRampColor(IndexedColor):
    """The color type used for NO_COLOR greyscale ramps.

    This implementation uses the color's perceived brightness as its base.
    """

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int]) -> GreyscaleRampColor:
        """Gets a greyscale color based on the given color's luminance."""

        color = cls("0")
        setattr(color, "_rgb", rgb)

        index = int(232 + color.brightness * 23)
        color.value = str(index)

        return color


@dataclass(repr=False)
class RGBColor(Color):
    """An arbitrary RGB color."""

    system = ColorSystem.TRUE

    def __post_init__(self) -> None:
        """Ensures data validity."""

        if self.value.count(";") != 2:
            raise ValueError(
                "Invalid value passed to RGBColor."
                + f" Format has to be rrr;ggg;bbb, got {self.value!r}."
            )

        rgb = tuple(int(num) for num in self.value.split(";"))
        self._rgb = rgb[0], rgb[1], rgb[2]

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int]) -> RGBColor:
        """Returns an `RGBColor` from the given triplet."""

        return cls(";".join(map(str, rgb)))

    @property
    def sequence(self) -> str:
        """Returns the ANSI sequence representing this color."""

        return (
            "\x1b["
            + ("48" if self.background else "38")
            + ";2;"
            + ";".join(str(num) for num in self.rgb)
            + "m"
        )


@dataclass
class HEXColor(RGBColor):
    """An arbitrary, CSS-like HEX color."""

    system = ColorSystem.TRUE

    def __post_init__(self) -> None:
        """Ensures data validity."""

        data = self.value
        if data.startswith("#"):
            data = data[1:]

        indices = (0, 2), (2, 4), (4, 6)
        rgb = []
        for start, end in indices:
            value = data[start:end]
            rgb.append(int(value, base=16))

        self._rgb = rgb[0], rgb[1], rgb[2]

        assert len(self._rgb) == 3


SYSTEM_TO_TYPE: dict[ColorSystem, Type[Color]] = {
    ColorSystem.NO_COLOR: GreyscaleRampColor,
    ColorSystem.STANDARD: StandardColor,
    ColorSystem.EIGHT_BIT: IndexedColor,
    ColorSystem.TRUE: RGBColor,
}


def _get_color_difference(
    rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]
) -> float:
    """Gets the geometric difference of 2 RGB colors (0-255).

    See https://en.wikipedia.org/wiki/Color_difference's Euclidian section.
    """

    red1, green1, blue1 = rgb1
    red2, green2, blue2 = rgb2

    redmean = (red1 + red2) // 2

    delta_red = red1 - red2
    delta_green = green1 - green2
    delta_blue = blue1 - blue2

    return sqrt(
        (2 + (redmean / 256)) * (delta_red**2)
        + 4 * (delta_green**2)
        + (2 + (255 - redmean) / 256) * (delta_blue**2)
    )


@lru_cache(maxsize=None)
def str_to_color(
    text: str,
    is_background: bool = False,
    localize: bool = True,
    use_cache: bool = False,
) -> Color:
    """Creates a `Color` from the given text.

    Accepted formats:
    - 0-255: `IndexedColor`.
    - 'rrr;ggg;bbb': `RGBColor`.
    - '(#)rrggbb': `HEXColor`. Leading hash is optional.

    You can also add a leading '@' into the string to make the output represent a
    background color, such as `@#123abc`.

    Args:
        text: The string to format from.
        is_background: Whether the output should be forced into a background color.
            Mostly used internally, when set will take precedence over syntax of leading
            '@' symbol.
        localize: Whether `get_localized` should be called on the output color.
        use_cache: Whether caching should be used.
    """

    def _trim_code(code: str) -> str:
        """Trims the given color code."""

        is_background = code.startswith("48;")

        if (code.startswith("38;5;") or code.startswith("48;5;")) or (
            code.startswith("38;2;") or code.startswith("48;2;")
        ):
            code = code[5:]

        if code.endswith("m"):
            code = code[:-1]

        if is_background:
            code = "@" + code

        return code

    text = _trim_code(text)

    if not use_cache:
        str_to_color.cache_clear()

    if text.startswith("@"):
        is_background = True
        text = text[1:]

    if text in NAMED_COLORS:
        return str_to_color(str(NAMED_COLORS[text]), is_background=is_background)

    color: Color

    # This code is not pretty, but having these separate branches for each type
    # should improve the performance by quite a large margin.
    match = RE_256.match(text)
    if match is not None:
        # Note: At the moment, all colors become an `IndexedColor`, due to a large
        #       amount of problems a separated `StandardColor` class caused. Not
        #       sure if there are any real drawbacks to doing it this way, bar the
        #       extra characters that 255 colors use up compared to xterm-16.
        color = IndexedColor(match[0], background=is_background)

        return color.get_localized() if localize else color

    match = RE_HEX.match(text)
    if match is not None:
        color = HEXColor(match[0], background=is_background).get_localized()

        return color.get_localized() if localize else color

    match = RE_RGB.match(text)
    if match is not None:
        color = RGBColor(match[0], background=is_background).get_localized()

        return color.get_localized() if localize else color

    raise ColorSyntaxError(f"Could not convert {text!r} into a `Color`.")


def foreground(text: str, color: str | Color, reset: bool = True) -> str:
    """Sets the foreground color of the given text.

    Note that the given color will be forced into `background = True`.

    Args:
        text: The text to color.
        color: The color to use. See `pytermgui.colors.str_to_color` for accepted
            str formats.
        reset: Whether the return value should include a reset sequence at the end.

    Returns:
        The colored text, including a reset if set.
    """

    if not isinstance(color, Color):
        color = str_to_color(color)

    color.background = False

    return color(text, reset=reset)


def background(text: str, color: str | Color, reset: bool = True) -> str:
    """Sets the background color of the given text.

    Note that the given color will be forced into `background = True`.

    Args:
        text: The text to color.
        color: The color to use. See `pytermgui.colors.str_to_color` for accepted
            str formats.
        reset: Whether the return value should include a reset sequence at the end.

    Returns:
        The colored text, including a reset if set.
    """

    if not isinstance(color, Color):
        color = str_to_color(color)

    color.background = True

    return color(text, reset=reset)
