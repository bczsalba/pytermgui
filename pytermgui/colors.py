"""https://stackoverflow.com/a/33206814"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from dataclasses import dataclass

from .exceptions import ColorSyntaxError
from .ansi_interface import reset as reset_style

if TYPE_CHECKING:
    from .parser import StyledText

__all__ = [
    "COLOR_TABLE",
    "XTERM_NAMED_COLORS",
    "NAMED_COLORS",
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

# Adapted from https://gist.github.com/MicahElliott/719710
COLOR_TABLE = {
    # 3 bit
    0: "000000",
    1: "800000",
    2: "008000",
    3: "808000",
    4: "000080",
    5: "800080",
    6: "008080",
    7: "c0c0c0",
    8: "808080",
    # Same colors, but bright
    9: "ff0000",
    10: "00ff00",
    11: "ffff00",
    12: "0000ff",
    13: "ff00ff",
    14: "00ffff",
    15: "ffffff",
    16: "000000",
    # xterm 256
    17: "00005f",
    18: "000087",
    19: "0000af",
    20: "0000d7",
    21: "0000ff",
    22: "005f00",
    23: "005f5f",
    24: "005f87",
    25: "005faf",
    26: "005fd7",
    27: "005fff",
    28: "008700",
    29: "00875f",
    30: "008787",
    31: "0087af",
    32: "0087d7",
    33: "0087ff",
    34: "00af00",
    35: "00af5f",
    36: "00af87",
    37: "00afaf",
    38: "00afd7",
    39: "00afff",
    40: "00d700",
    41: "00d75f",
    42: "00d787",
    43: "00d7af",
    44: "00d7d7",
    45: "00d7ff",
    46: "00ff00",
    47: "00ff5f",
    48: "00ff87",
    49: "00ffaf",
    50: "00ffd7",
    51: "00ffff",
    52: "5f0000",
    53: "5f005f",
    54: "5f0087",
    55: "5f00af",
    56: "5f00d7",
    57: "5f00ff",
    58: "5f5f00",
    59: "5f5f5f",
    60: "5f5f87",
    61: "5f5faf",
    62: "5f5fd7",
    63: "5f5fff",
    64: "5f8700",
    65: "5f875f",
    66: "5f8787",
    67: "5f87af",
    68: "5f87d7",
    69: "5f87ff",
    70: "5faf00",
    71: "5faf5f",
    72: "5faf87",
    73: "5fafaf",
    74: "5fafd7",
    75: "5fafff",
    76: "5fd700",
    77: "5fd75f",
    78: "5fd787",
    79: "5fd7af",
    80: "5fd7d7",
    81: "5fd7ff",
    82: "5fff00",
    83: "5fff5f",
    84: "5fff87",
    85: "5fffaf",
    86: "5fffd7",
    87: "5fffff",
    88: "870000",
    89: "87005f",
    90: "870087",
    91: "8700af",
    92: "8700d7",
    93: "8700ff",
    94: "875f00",
    95: "875f5f",
    96: "875f87",
    97: "875faf",
    98: "875fd7",
    99: "875fff",
    100: "878700",
    101: "87875f",
    102: "878787",
    103: "8787af",
    104: "8787d7",
    105: "8787ff",
    106: "87af00",
    107: "87af5f",
    108: "87af87",
    109: "87afaf",
    110: "87afd7",
    111: "87afff",
    112: "87d700",
    113: "87d75f",
    114: "87d787",
    115: "87d7af",
    116: "87d7d7",
    117: "87d7ff",
    118: "87ff00",
    119: "87ff5f",
    120: "87ff87",
    121: "87ffaf",
    122: "87ffd7",
    123: "87ffff",
    124: "af0000",
    125: "af005f",
    126: "af0087",
    127: "af00af",
    128: "af00d7",
    129: "af00ff",
    130: "af5f00",
    131: "af5f5f",
    132: "af5f87",
    133: "af5faf",
    134: "af5fd7",
    135: "af5fff",
    136: "af8700",
    137: "af875f",
    138: "af8787",
    139: "af87af",
    140: "af87d7",
    141: "af87ff",
    142: "afaf00",
    143: "afaf5f",
    144: "afaf87",
    145: "afafaf",
    146: "afafd7",
    147: "afafff",
    148: "afd700",
    149: "afd75f",
    150: "afd787",
    151: "afd7af",
    152: "afd7d7",
    153: "afd7ff",
    154: "afff00",
    155: "afff5f",
    156: "afff87",
    157: "afffaf",
    158: "afffd7",
    159: "afffff",
    160: "d70000",
    161: "d7005f",
    162: "d70087",
    163: "d700af",
    164: "d700d7",
    165: "d700ff",
    166: "d75f00",
    167: "d75f5f",
    168: "d75f87",
    169: "d75faf",
    170: "d75fd7",
    171: "d75fff",
    172: "d78700",
    173: "d7875f",
    174: "d78787",
    175: "d787af",
    176: "d787d7",
    177: "d787ff",
    178: "d7af00",
    179: "d7af5f",
    180: "d7af87",
    181: "d7afaf",
    182: "d7afd7",
    183: "d7afff",
    184: "d7d700",
    185: "d7d75f",
    186: "d7d787",
    187: "d7d7af",
    188: "d7d7d7",
    189: "d7d7ff",
    190: "d7ff00",
    191: "d7ff5f",
    192: "d7ff87",
    193: "d7ffaf",
    194: "d7ffd7",
    195: "d7ffff",
    196: "ff0000",
    197: "ff005f",
    198: "ff0087",
    199: "ff00af",
    200: "ff00d7",
    201: "ff00ff",
    202: "ff5f00",
    203: "ff5f5f",
    204: "ff5f87",
    205: "ff5faf",
    206: "ff5fd7",
    207: "ff5fff",
    208: "ff8700",
    209: "ff875f",
    210: "ff8787",
    211: "ff87af",
    212: "ff87d7",
    213: "ff87ff",
    214: "ffaf00",
    215: "ffaf5f",
    216: "ffaf87",
    217: "ffafaf",
    218: "ffafd7",
    219: "ffafff",
    220: "ffd700",
    221: "ffd75f",
    222: "ffd787",
    223: "ffd7af",
    224: "ffd7d7",
    225: "ffd7ff",
    226: "ffff00",
    227: "ffff5f",
    228: "ffff87",
    229: "ffffaf",
    230: "ffffd7",
    231: "ffffff",
    # Gray-scale
    232: "080808",
    233: "121212",
    234: "1c1c1c",
    235: "262626",
    236: "303030",
    237: "3a3a3a",
    238: "444444",
    239: "4e4e4e",
    240: "585858",
    241: "626262",
    242: "6c6c6c",
    243: "767676",
    244: "808080",
    245: "8a8a8a",
    246: "949494",
    247: "9e9e9e",
    248: "a8a8a8",
    249: "b2b2b2",
    250: "bcbcbc",
    251: "c6c6c6",
    252: "d0d0d0",
    253: "dadada",
    254: "e4e4e4",
    255: "eeeeee",
}

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


@dataclass
class Color:
    """A terminal color.

    Args:
        value: The data contained within this color.
        background: Whether this color will represent a color.
    """

    value: str
    background: bool = False

    @property
    def sequence(self) -> str:
        """Returns the ANSI sequence representation of the color."""

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Returns this color as a tuple of (red, green, blue) values."""

    @property
    def name(self) -> str:
        """Returns the reverse-parseable name of this color."""

        return ("@" if self.background else "") + self.value

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
        """Creates a terminal-capability local Color instance."""

        return self


@dataclass
class IndexedColor(Color):
    """A color representing an index into the xterm-256 color palette."""

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

    @property
    def sequence(self) -> str:
        r"""Returns an ANSI sequence representing this color."""

        index = int(self.value)

        if index >= 16:
            return "\x1b[" + ("48" if self.background else "38") + f";5;{index}m"

        if index <= 7:
            index += 30

        else:
            index = index + 82

        if self.background:
            index += 10

        return f"\x1b[{index}m"

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Returns an RGB representation of this color."""

        index = int(self.value)
        hexc = COLOR_TABLE[index]

        rgb = []
        for i in (0, 2, 4):
            rgb.append(int(hexc[i : i + 2], base=16))

        return (rgb[0], rgb[1], rgb[2])


@dataclass
class RGBColor(Color):
    """An arbitrary RGB color."""

    def __post_init__(self) -> None:
        """Ensures data validity."""

        if not self.value.count(";") == 2:
            raise ValueError(
                "Invalid value passed to RGBColor."
                + f" Format has to be rrr;ggg;bbb, got {self.value!r}."
            )

        self._rgb = tuple(int(num) for num in self.value.split(";"))

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Returns the RGB representation of this color."""

        return self._rgb[0], self._rgb[1], self._rgb[2]

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

        self._rgb = tuple(rgb)

        assert len(self._rgb) == 3


def str_to_color(text: str, is_background: bool = False) -> Color:
    """Creates a `Color` from the given text.

    Accepted formats:
    - 0-255: `IndexedColor`.
    - 'rrr;ggg;bbb': `RGBColor`.
    - '(#)rrggbb': `HEXColor`. Leading hash is optional.

    Args:
        text: The string to format from.
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

    if text.startswith("@"):
        is_background = True
        text = text[1:]

    if text in NAMED_COLORS:
        return str_to_color(NAMED_COLORS[text], is_background=is_background)

    match = RE_256.match(text)
    if match is not None:
        index = int(match[0])

        return IndexedColor(str(index), background=is_background)

    match = RE_HEX.match(text)
    if match is not None:
        return HEXColor(match[0], background=is_background)

    match = RE_RGB.match(text)
    if match is not None:
        return RGBColor(match[0], background=is_background)

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
