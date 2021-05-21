"""
pytermgui.parser
----------------
author: bczsalba


This module provides a class to parse rich text formatted strings into
ANSI text, and the reverse."""

import sys
from typing import Optional, Callable, no_type_check

from .ansi_interface import (
    bold,
    reset,
    dim,
    italic,
    underline,
    blinking,
    inverse,
    invisible,
    strikethrough,
    foreground as color,
    background as color_bg,
)

__all__ = ["ColorParser"]

FunctionType = Callable[[str, Optional[bool]], str]
FunctionDict = dict[str, FunctionType]


class ColorParser:
    """This class parses rich text and ANSI containing strings
    back and forth.

    The basic usage is:
        ```
        >>> parser = ColorParser()
        >>> ansi = parser.parse("[@60 141 bold]this is rich text[/]")
        "\\x1b[0m\\x1b[48;5;60m\\x1b[38;5;141m\\x1b[1mthis is rich text\\x1b[0m"

        >>> rich = parser.inverse_parse(ansi)
        "[@60 141 bold]this is rich text[/]"
        ```

    Notes about syntax:
        Because of the way the function calls work, the first applied color will take
        precedence over any that are applied to the same "channel" (foreground/background).

        For example, "[141 60 @60]text[/]" will apply background color 60, and foreground color
        141, while ignoring the foreground 60.

    Rich text tokens:
        - basic styling:
            [bold]
            [dim]
            [italic]
            [underline]
            [blinking]
            [inverse]
            [invisible]
            [strikethrough]

        - colors:
            black                      - color code 0
            red                        - color code 1
            green                      - color code 2
            yellow                     - color code 3
            blue                       - color code 4
            magenta                    - color code 5
            cyan                       - color code 6
            white                      - color code 7

            [{0-255}]                  - 8-bit colors
            [{0-255};{0-255};{0-255}]  - 24-bit (rgb) colors
            [#{123456}]                - hex colors
            [@{color}]                 - background version of one of the above

        - modifiers & misc:
        *: TODO
            [/]                        - clear all styles
            *[/color]                  - clear colors, leave style
            *[/style]                  - clear style, leave colors

    The object also takes an optional dict[str, FunctionType] for token calls,
    which allows you to completely redefine what it parses and how. Not sure why,
    but hey, you can.
    """

    def __init__(self, token_map: Optional[FunctionDict] = None) -> None:
        """Initialize object"""

        if token_map is None:
            self.token_map: FunctionDict = {
                "bold": bold,
                "dim": dim,
                "italic": italic,
                "underline": underline,
                "blinking": blinking,
                "inverse": inverse,
                "invisible": invisible,
                "strikethrough": strikethrough,
            }

        else:
            self.token_map = token_map.copy()

        self.tokens = list(self.token_map.keys())

        self._color_functions: FunctionDict = {}

    @staticmethod
    def _peek(value: str, index: int) -> Optional[str]:
        """Show next (+ index) character"""

        if index < len(value):
            return value[index]

        return None

    @staticmethod
    def _apply(functions: list[FunctionType], value: str) -> str:
        """Apply functions to value"""

        for function in reversed(functions):
            value = function(value, False).rstrip(reset())

        return value

    def _clear_colors(self, attributes: list[FunctionType]) -> None:
        """Clear all color attributes"""

        for function in self._color_functions.values():
            attributes.remove(function)

    @no_type_check
    def _check_for_color(self, token: str) -> list[FunctionType]:
        """Check for color in token and return callables if found
        Mypy cannot infern the type of the lambdas used here."""

        def _create_color(clr: str) -> int:
            """Return integer from color and check if valid"""

            numbers = [int(number) for number in list(clr)]

            if len(numbers) > 3:
                raise NotImplementedError(
                    "Color values are constrained to range [0; 256]."
                )

            while not len(numbers) == 3:
                numbers.insert(0, 0)

            first, second, third = numbers
            number = first * 100 + second * 10 + third

            if number > 256:
                raise NotImplementedError(
                    "Color values are constrained to range [0; 256]."
                )

            return number

        def _add_callable(function: FunctionType) -> list[FunctionType]:
            """Add callable to self._color_functions and return same object"""

            self._color_functions[token] = function
            return [function]

        if token.startswith("@"):
            token = token[1:]
            color_fun = color_bg
        else:
            color_fun = color

        if token in color_fun.names:
            name_function: FunctionType = lambda item, _: color_fun(item, token)
            return _add_callable(name_function)

        values = token.split(";")

        if token.startswith("#"):
            hex_function: FunctionType = lambda item, _: color_fun(item, token)
            return _add_callable(hex_function)

        out = []
        for value in values:
            if not all(char.isdigit() for char in value):
                return []

            out.append(_create_color(value))

        if len(out) == 1:
            color_function: FunctionType = lambda item, _: color_fun(item, out[0])
            return _add_callable(color_function)

        rgb_function: FunctionType = lambda item, _: color_fun(item, tuple(out))
        return _add_callable(rgb_function)

    def inverse_parse(self, value: str) -> str:
        """Parse formatted value to a string that can be `parse`-d to the original"""

        def _convert_sequence(seq: str) -> str:
            """Convert ANSI sequence into parsable string"""

            if seq == reset():
                if len(out) > 1:
                    return "/"
                return ""

            if seq in targets.keys():
                return targets[seq]

            maybe_colors = seq[seq.find("[") + 1 : seq.rfind(reset())].split(";")
            attrs = ";".join(maybe_colors[2:])

            if attrs.isdigit() and int(attrs) in color.names.values():
                for key, value in color.names.items():
                    if value == int(attrs):
                        return key

            if attrs == "0":
                return ""

            if maybe_colors[0] == "48":
                attrs = "@" + attrs

            return attrs

        targets = {value("", False): key for key, value in self.token_map.items()}
        in_sequence = False
        current_sequence = ""
        join_attrs = False
        out = ""
        old = None

        for i, char in enumerate(value):
            if in_sequence:
                current_sequence += char

                if char == "m":
                    in_sequence = False
                    new = _convert_sequence("\x1b" + current_sequence)

                    if not new == old:
                        join_attrs = self._peek(value, i + 1) == "\x1b"
                        padding = " " if len(new) > 0 else ""

                        out += new + (padding if join_attrs > 0 else "]")

                    current_sequence = ""
                    old = new
                    continue

                continue

            if char == "\x1b":
                if not join_attrs and not out.endswith("["):
                    out += "["

                in_sequence = True
                continue

            out += char

        self._color_functions = {}
        return out

    # pylint: disable=too-many-statements,too-many-branches
    def parse(self, value: str) -> str:
        """Parse value and create string with applied attributes

        Less statements & branches would mean the function would have to be
        split into even more smaller parts, which would ruin readability."""

        def _parse_token(
            token: str, attributes: list[FunctionType], removing_attr: bool
        ) -> None:
            """Parse token and add it to attributes"""

            if token in self.tokens or token in self._color_functions:
                if token in self._color_functions:
                    function = self._color_functions[token]
                    del self._color_functions[token]
                else:
                    function = self.token_map[token]

                if removing_attr:
                    attributes.remove(function)
                else:
                    attributes.append(function)

        token = ""
        attributes: list[FunctionType] = []
        old_attributes: list[FunctionType] = []
        out = ""

        in_attr = False
        removing_attr = False
        background_color = False

        def _reset_values() -> None:
            """Reset token, removing_attr, background_color,
            run self._check_for_color(token)

            This function is below var definitions because of issues
            from unbound non-locals."""

            nonlocal removing_attr, background_color, token, attributes

            if not removing_attr:
                attributes += self._check_for_color(token)

            removing_attr = False
            background_color = False
            token = ""

        for i, char in enumerate(value):
            if in_attr:
                if char == "/":
                    removing_attr = True

                    # remove all attributes
                    if self._peek(value, i + 1) in [" ", "]"]:
                        attributes = []
                        self._color_functions = {}
                        out += reset()

                    continue

                if char == "]":
                    in_attr = False
                    _reset_values()
                    continue

                if char == " ":
                    _reset_values()
                    continue

                token += char
                if removing_attr and token == "color":
                    self._clear_colors(attributes)
                    self._color_functions = {}

                elif removing_attr and token == "style":
                    for function in attributes:
                        if not function in self._color_functions.values():
                            attributes.remove(function)

                _parse_token(token, attributes, removing_attr)
                continue

            if char == "[":
                in_attr = True
                continue

            if not old_attributes == attributes:
                new = [attr for attr in attributes if attr not in old_attributes]
                out += self._apply(new, char)

            else:
                out += char

            old_attributes = attributes.copy()

        self._color_functions = {}
        return out + reset()


if __name__ == "__main__":
    # "[italic bold 141;35;60]hello there[/][141] alma[/] [18;218;168 underline]fa"

    from argparse import ArgumentParser

    argparser = ArgumentParser()
    argparser.add_argument("parsed_text", help="parse string into ansi text")
    argparser.add_argument(
        "--inverse", help="inverse parse string into rich string", action="store_true"
    )
    argparser.add_argument(
        "-e", "--escape", help="show output with escaped codes", action="store_true"
    )
    arguments = argparser.parse_args()

    parser = ColorParser()
    if arguments.inverse:
        rich_to_parsed = parser.inverse_parse(arguments.parsed_text)
        print(rich_to_parsed)
        print(parser.parse(rich_to_parsed))

    elif arguments.parsed_text:
        parsed = parser.parse(arguments.parsed_text)
        if arguments.escape:
            print(parsed.encode("unicode_escape").decode("utf-8"))
        else:
            print(parsed)

        parsed_to_rich = parser.inverse_parse(parsed)
        print(parsed_to_rich)
        print(parser.parse(parsed_to_rich))

    else:
        argparser.print_help(sys.stderr)
        sys.exit(1)
