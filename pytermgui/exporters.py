"""This module provides various methods and utilities to turn TIM into HTML."""

from __future__ import annotations

from html import escape
from typing import Iterator

from .colors import Color
from .widgets import Widget
from .terminal import get_terminal
from .parser import Token, TokenType, StyledText, tim

MARGIN = 15
BODY_MARGIN = 70
CHAR_WIDTH = 0.62
CHAR_HEIGHT = 1.15
FONT_SIZE = 15

HTML_FORMAT = """\
<html>
    <head>
        <style>
            body {{
                --ptg-background: {background};
                --ptg-foreground: {foreground};
                color: var(--ptg-foreground);
                background-color: var(--ptg-background);
            }}
            a {{
                text-decoration: none;
                color: inherit;
            }}
            code {{
                font-size: {font_size}px;
                font-family: Menlo, 'DejaVu Sans Mono', consolas, 'Courier New', monospace;
                line-height: 1.2em;
            }}
            .ptg-position {{
                position: absolute;
            }}
{styles}
        </style>
    </head>
    <body>
        <pre class="ptg">
            <code>
{content}
            </code>
        </pre>
    </body>
</html>"""

SVG_FORMAT = """\
<svg width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}"
     xmlns="http://www.w3.org/2000/svg">
    <style>
        body {{
            --ptg-background: {background};
            --ptg-foreground: {foreground};
            color: var(--ptg-foreground);
            margin: {body_margin}px;
        }}
        span {{
            display: inline-block;
        }}
        code {{
            font-family: Menlo, 'DejaVu Sans Mono', consolas, 'Courier New', monospace;
            line-height: 1.2em;
        }}
        a {{
            text-decoration: none;
            color: inherit;
        }}
        #ptg-terminal {{
            position: relative;
            display: flex;
            flex-direction: column;
            background-color: var(--ptg-background);
            border-radius: 9px;
            box-shadow: 0 22px 70px 4px rgba(0, 0, 0, 0.56);
            width: {margined_width}px;
            height: {margined_height}px;
        }}
        #ptg-terminal-navbuttons {{
            position: absolute;
            top: 8px;
            left: 8px;
        }}
        #ptg-terminal-body {{
            margin: 15px;
            font-size: {font_size}px;
            overflow: hidden scroll;
            white-space: normal;
        }}
        #ptg-terminal-title {{
            font-family: sans-serif;
            font-size: 12px;
            font-weight: bold;
            color: #95989b;
            margin-top: 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .ptg-position {{
            position: absolute;
        }}
{styles}
    </style>
    <foreignObject width="100%" height="100%" x="0" y="0">
        <body xmlns="http://www.w3.org/1999/xhtml">
            <div id="ptg-terminal">
                <svg id="ptg-terminal-navbuttons" width="90" height="21"
                  viewBox="0 0 90 21" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="8" cy="6" r="6" fill="#ff6159"/>
                    <circle cx="28" cy="6" r="6" fill="#ffbd2e"/>
                    <circle cx="48" cy="6" r="6" fill="#28c941"/>
                </svg>
                <div id="ptg-terminal-title">{title}</div>
                <pre id="ptg-terminal-body">
                    <code>
{content}
                    </code>
                </pre>
            </div>
        </body>
    </foreignObject>
</svg>"""

_STYLE_TO_CSS = {
    "bold": "font-weight: bold",
    "italic": "font-style: italic",
    "dim": "opacity: 0.7",
    "underline": "text-decoration: underline",
    "strikethrough": "text-decoration: line-through",
    "overline": "text-decoration: overline",
}


__all__ = ["token_to_css", "to_html"]


def _get_cls(prefix: str | None, index: int) -> str:
    """Constructs a class identifier with the given prefix and index."""

    return "ptg" + ("-" + prefix if prefix is not None else "") + str(index)


def _generate_stylesheet(document_styles: list[list[str]], prefix: str | None) -> str:
    """Generates a '\\n' joined CSS stylesheet from the given styles."""

    stylesheet = ""
    for i, styles in enumerate(document_styles):
        stylesheet += "\n." + _get_cls(prefix, i) + " {" + "; ".join(styles) + "}"

    return stylesheet


def _generate_index_in(lst: list[list[str]], item: list[str]) -> int:
    """Returns the given item's index in the list, len(lst) if not found."""

    index = len(lst)

    if item in lst:
        return lst.index(item)

    return index


# Note: This whole routine will be massively refactored in an upcoming update,
#       once StyledText has a bit of a better way of managing style attributes.
#       Until then we must ignore some linting issues :(.
def _get_spans(  # pylint: disable=too-many-locals
    line: str,
    vertical_offset: float,
    horizontal_offset: float,
    include_background: bool,
) -> Iterator[tuple[str, list[str]]]:
    """Creates `span` elements from the given line, yields them with their styles.

    Args:
        line: The ANSI line of text to use.

    Yields:
        Tuples of the span text (more on that later), and a list of CSS styles applied
        to it.  The span text is in the format `<span{}>content</span>`, and it doesn't
        yet have the styles formatted into it.
    """

    def _adjust_pos(
        position: int, scale: float, offset: float, digits: int = 2
    ) -> float:
        """Adjusts a given position for the HTML canvas' scale."""

        return round(position * scale + offset / FONT_SIZE, digits)

    position = None

    for styled in tim.get_styled_plains(line):
        styles = []
        if include_background:
            styles.append("background-color: var(--ptg-background)")

        has_link = False
        has_inverse = False

        for token in sorted(
            styled.tokens, key=lambda token: token.ttype is TokenType.COLOR
        ):
            if token.ttype is TokenType.PLAIN:
                continue

            if token.ttype is TokenType.POSITION:
                assert isinstance(token.data, str)

                if token.data != position:
                    # Yield closer if there is already an active positioner
                    if position is not None:
                        yield "</div>", []

                    position = token.data
                    split = tuple(map(int, position.split(",")))

                    adjusted = (
                        _adjust_pos(split[0], CHAR_WIDTH, horizontal_offset),
                        _adjust_pos(split[1], CHAR_HEIGHT, vertical_offset),
                    )

                    yield (
                        "<div class='ptg-position'"
                        + f" style='left: {adjusted[0]}em; top: {adjusted[1]}em'>"
                    ), []

            elif token.ttype is TokenType.LINK:
                has_link = True
                yield f"<a href='{token.data}'>", []

            elif token.ttype is TokenType.STYLE and token.name == "inverse":
                has_inverse = True

                # Add default inverted colors, in case the text doesn't have any
                # color applied.
                styles.append("color: var(--ptg-background);")
                styles.append("background-color: var(--ptg-foreground)")

                continue

            css = token_to_css(token, has_inverse)
            if css is not None and css not in styles:
                styles.append(css)

        escaped = (
            escape(styled.plain)
            .replace("{", "{{")
            .replace("}", "}}")
            .replace(" ", "&#160;")
        )

        if len(styles) == 0:
            yield f"<span>{escaped}</span>", []
            continue

        tag = "<span{}>" + escaped + "</span>"
        tag += "</a>" if has_link else ""

        yield tag, styles


def token_to_css(token: Token, invert: bool = False) -> str:
    """Finds the CSS representation of a token.

    Args:
        token: The token to represent.
        invert: If set, the role of background & foreground colors
            are flipped.
    """

    if token.ttype is TokenType.COLOR:
        color = token.data
        assert isinstance(color, Color)

        style = "color:" + color.hex

        if invert:
            color.background = not color.background

        if color.background:
            style = "background-" + style

        return style

    if token.ttype is TokenType.STYLE and token.name in _STYLE_TO_CSS:
        return _STYLE_TO_CSS[token.name]

    return ""


# We take this many arguments for future proofing and customization, not much we can
# do about it.
def to_html(  # pylint: disable=too-many-arguments, too-many-locals
    obj: Widget | StyledText | str,
    prefix: str | None = None,
    inline_styles: bool = False,
    include_background: bool = True,
    vertical_offset: float = 0.0,
    horizontal_offset: float = 0.0,
    formatter: str = HTML_FORMAT,
    joiner: str = "\n",
) -> str:
    """Creates a static HTML representation of the given object.

    Note that the output HTML will not be very attractive or easy to read. This is
    because these files probably aren't meant to be read by a human anyways, so file
    sizes are more important.

    If you do care about the visual style of the output, you can run it through some
    prettifiers to get the result you are looking for.

    Args:
        obj: The object to represent. Takes either a Widget or some markup text.
        prefix: The prefix included in the generated classes, e.g. instead of `ptg-0`,
            you would get `ptg-my-prefix-0`.
        inline_styles: If set, styles will be set for each span using the inline `style`
            argument, otherwise a full style section is constructed.
        include_background: Whether to include the terminal's background color in the
            output.
    """

    document_styles: list[list[str]] = []

    if isinstance(obj, Widget):
        data = obj.get_lines()

    else:
        data = obj.splitlines()

    lines = []
    for dataline in data:
        line = ""

        for span, styles in _get_spans(
            dataline, vertical_offset, horizontal_offset, include_background
        ):
            index = _generate_index_in(document_styles, styles)
            if index == len(document_styles):
                document_styles.append(styles)

            if inline_styles:
                stylesheet = ";".join(styles)
                line += span.format(f" styles='{stylesheet}'")

            else:
                line += span.format(" class='" + _get_cls(prefix, index) + "'")

        # Close any previously not closed divs
        line += "</div>" * (line.count("<div") - line.count("</div"))
        lines.append(line)

    stylesheet = ""
    if not inline_styles:
        stylesheet = _generate_stylesheet(document_styles, prefix)

    document = formatter.format(
        foreground=Color.get_default_foreground().hex,
        background=Color.get_default_background().hex if include_background else "",
        content=joiner.join(lines),
        styles=stylesheet,
        font_size=FONT_SIZE,
    )

    return document


def to_svg(
    obj: Widget | StyledText | str,
    prefix: str | None = None,
    inline_styles: bool = False,
    title: str = "PyTermGUI",
    formatter: str = SVG_FORMAT,
) -> str:
    """Creates an SVG screenshot of the given object.

    This screenshot tries to mimick what the Kitty terminal looks like on MacOS,
    complete with the menu buttons and drop shadow. The `title` argument will be
    displayed in the window's top bar.

    Args:
        obj: The object to represent. Takes either a Widget or some markup text.
        prefix: The prefix included in the generated classes, e.g. instead of `ptg-0`,
            you would get `ptg-my-prefix-0`.
        inline_styles: If set, styles will be set for each span using the inline `style`
            argument, otherwise a full style section is constructed.
        title: A string to display in the top bar of the fake terminal.
        formatter: The formatting string to use. Inspect `pytermgui.exporters.SVG_FORMAT`
            to see all of its arguments.
    """

    terminal = get_terminal()
    width = terminal.width * FONT_SIZE * CHAR_WIDTH + MARGIN + 10
    height = terminal.height * FONT_SIZE * CHAR_HEIGHT + 105

    formatter = formatter.replace("{body_margin}", str(BODY_MARGIN))

    total_width = width + 2 * MARGIN + 2 * BODY_MARGIN
    formatter = formatter.replace("{total_width}", str(total_width))

    total_height = height + 2 * MARGIN + 2 * BODY_MARGIN
    formatter = formatter.replace("{total_height}", str(total_height))

    formatter = formatter.replace("{margined_width}", str(width))
    formatter = formatter.replace("{margined_height}", str(height))
    formatter = formatter.replace("{title}", title)

    return to_html(
        obj,
        prefix=prefix,
        inline_styles=inline_styles,
        formatter=formatter,
        vertical_offset=5 + MARGIN,
        horizontal_offset=MARGIN,
        joiner="\n<br />",
    )
