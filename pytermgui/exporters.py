"""This module provides various methods and utilities to turn TIM into HTML."""

from __future__ import annotations

from html import escape
from typing import Iterator

from .colors import Color
from .widgets import Widget
from .terminal import terminal
from .parser import Token, TokenType, StyledText, tim

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
            pre {{
                font-size: 15px;
                font-family: Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace;
            }}
{styles}
        </style>
    </head>
    <body>
        <pre class="ptg">
{content}
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
            background-color: var(--ptg-background);
        }}
        span {{
            display: inline-block;
        }}
        pre {{
            font-family: Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace;
            font-size: 15px;
        }}
        a {{
            text-decoration: none;
            color: inherit;
        }}
        .blink {{
           animation: blinker 1s infinite;
        }}
        @keyframes blinker {{
            from {{ opacity: 1.0; }}
            50% {{ opacity: 0.3; }}
            to {{ opacity: 1.0; }}
        }}
        {styles}
    </style>
    <rect width="100%" height="100%" fill="{background}" />
    <foreignObject x="0" y="0" width="100%" height="100%">
        <body xmlns="http://www.w3.org/1999/xhtml">
            <pre class="ptg">
                {content}
            </pre>
        </body>
    </foreignObject>
</svg>
"""

_STYLE_TO_CSS = {
    "bold": "font-weight: bold",
    "italic": "font-style: italic",
    "dim": "filter: brightness(70%)",
    "underline": "text-decoration: underline",
    "strikethrough": "text-decoration: line-through",
    "overline": "text-decoration: overline",
}


__all__ = ["token_to_css", "to_html"]


def _get_cls(prefix: str | None, index: int) -> str:
    """Constructs a class identifier with the given prefix and index."""

    return "ptg" + ("-" + prefix if prefix is not None else "") + str(index)


def _get_spans(line: str) -> Iterator[tuple[str, list[str]]]:
    """Creates `span` elements from the given line, yields them with their styles.

    Args:
        line: The ANSI line of text to use.

    Yields:
        Tuples of the span text (more on that later), and a list of CSS styles applied to it.
        The span text is in the format `<span{}>content</span>`, and it doesn't have the styles
        formatted into it.
    """

    position = None
    nest_count = 0
    for styled in tim.get_styled_plains(line):
        styles = ["background-color: var(--ptg-background)"]

        has_link = False
        has_inverse = False

        for token in styled.tokens:
            if token.ttype is TokenType.PLAIN:
                continue

            if token.ttype is TokenType.POSITION:
                assert isinstance(token.data, str)
                if token.data != position:
                    position = token.data
                    split = position.split(",")
                    adjusted = (
                        round(int(split[0]) * 0.5, 2),
                        round(int(split[1]) * 1.15, 2),
                    )

                    yield (
                        "<div style='position: fixed;"
                        + "left: {}em; top: {}em'>".format(*adjusted)
                    ), []
                    nest_count += 1

            elif token.ttype is TokenType.LINK:
                has_link = True
                yield f"<a href='{token.data}'>", []

            elif token.ttype is TokenType.STYLE and token.name == "inverse":
                has_inverse = True
                continue

            css = token_to_css(token, has_inverse)
            if css is not None and css not in styles:
                styles.append(css)

        escaped = escape(styled.plain)

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


def to_html(
    obj: Widget | StyledText | str,
    prefix: str | None = None,
    inline_styles: bool = False,
    formatter: str = HTML_FORMAT,
) -> str:
    """Creates a static HTML representation of the given object.

    Note that the output HTML will not be very attractive or easy to read. This is because
    these files probably aren't meant to be read by a human anyways, so file sizes are more
    important.

    If you do care about the visual style of the output, you can run it through some prettifiers
    to get the result you are looking for.

    Args:
        obj: The object to represent. Takes either a Widget or some markup text.
        prefix: The prefix included in the generated classes, e.g. instead of `ptg-0`,
            you would get `ptg-my-prefix-0`.
        inline_styles: If set, styles will be set for each span using the inline `style`
            argument, otherwise a full style section is constructed.
    """

    document_styles: list[list[str]] = []

    if isinstance(obj, Widget):
        data = obj.get_lines()

    else:
        data = obj.splitlines()

    lines = []
    for dataline in data:
        line = ""

        for span, styles in _get_spans(dataline):
            index = len(document_styles)

            if styles in document_styles:
                index = document_styles.index(styles)
            else:
                document_styles.append(styles)

            if inline_styles:
                stylesheet = ";".join(styles)
                line += span.format(" styles='{stylesheet}'")

            else:
                line += span.format(" class='" + _get_cls(prefix, index) + "'")

        line += "</div>" * line.count("div")
        lines.append(line)

    stylesheet = ""
    if not inline_styles:
        for i, styles in enumerate(document_styles):
            stylesheet += "\n." + _get_cls(prefix, i) + " {" + "; ".join(styles) + "}"

    document = formatter.format(
        foreground=Color.get_default_foreground().hex,
        background=Color.get_default_background().hex,
        content="\n".join(lines),
        styles=stylesheet,
    )

    return document


def to_svg(
    obj: Widget | StyledText | str,
    prefix: str | None = None,
    inline_styles: bool = False,
    formatter: str = SVG_FORMAT,
) -> str:
    """Creates an SVG representation of the given object.

    Note that the output SVG will not be very attractive or easy to read. This is because
    these files probably aren't meant to be read by a human anyways, so file sizes are more
    important.

    If you do care about the visual style of the output, you can run it through some prettifiers
    to get the result you are looking for.

    Args:
        obj: The object to represent. Takes either a Widget or some markup text.
        prefix: The prefix included in the generated classes, e.g. instead of `ptg-0`,
            you would get `ptg-my-prefix-0`.
        inline_styles: If set, styles will be set for each span using the inline `style`
            argument, otherwise a full style section is constructed.
    """

    formatter = formatter.replace("{total_width}", str(terminal.pixel_size[0]))
    formatter = formatter.replace("{total_height}", str(terminal.pixel_size[1]))

    return to_html(obj, prefix=prefix, inline_styles=inline_styles, formatter=formatter)
