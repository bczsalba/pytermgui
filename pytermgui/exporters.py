"""This module provides various methods and utilities to turn TIM into HTML."""

from __future__ import annotations

from html import escape
from typing import Iterator

from .colors import Color
from .widgets import Widget
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

_STYLE_TO_CSS = {
    "bold": "font-weight: bold",
    "italic": "font-style: italic",
    "dim": "filter: brightness(70%)",
    "underline": "text-decoration: underline",
    "strikethrough": "text-decoration: line-through",
    "overline": "text-decoration: overline",
}


__all__ = ["token_to_css", "to_html"]


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

    def _get_cls(index: int) -> str:
        """Constructs a class identifier with the given prefix and index."""

        return "ptg" + ("-" + prefix if prefix is not None else "") + str(index)

    def _get_spans(line: str) -> Iterator[str]:
        """Creates `span` elements from the given line."""

        position = None
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
                        adjusted = tuple(
                            (
                                round(val, 2)
                                for val in (int(split[0]) * 0.5, 1.1 * int(split[1]))
                            )
                        )

                        yield (
                            "<div style='position: fixed;"
                            + "left: {}em; top: {}em'>".format(*adjusted)
                        )

                elif token.ttype is TokenType.LINK:
                    has_link = True
                    yield f"<a href='{token.data}'>"

                elif token.ttype is TokenType.STYLE and token.name == "inverse":
                    has_inverse = True
                    continue

                css = token_to_css(token, has_inverse)
                if css is not None and css not in styles:
                    styles.append(css)

            escaped = escape(styled.plain)

            if len(styles) == 0:
                yield f"<span>{escaped}</span>"
                continue

            index = len(document_styles)
            if styles in document_styles:
                index = document_styles.index(styles)
            else:
                document_styles.append(styles)

            value = ";".join(styles) if inline_styles else _get_cls(index)
            prefix = "style" if inline_styles else "class"

            tag = f"<span {prefix}='{value}'>{escaped}</span>"
            tag += "</a>" if has_link else ""

            yield tag

    if isinstance(obj, Widget):
        data = obj.get_lines()

    else:
        data = obj.splitlines()

    lines = []
    for line in data:
        lines.append("".join(_get_spans(line)))

    content = "\n".join(lines)

    styles = ""
    if not inline_styles:
        styles += "\n".join(
            f".{_get_cls(i)} {{{';'.join(style)}}}"
            for i, style in enumerate(document_styles)
        )

    document = HTML_FORMAT.format(
        foreground=Color.get_default_foreground().hex,
        background=Color.get_default_background().hex,
        content=content,
        styles=styles,
    )

    return document
