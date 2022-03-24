"""This module provides various methods and utilities to turn TIM into HTML."""

from __future__ import annotations

from html import escape
from typing import Iterator

from .colors import Color
from .widgets import Widget
from .parser import Token, TokenType, StyledText, tim

BASE_HTML = """\
<html>
    <head>
        <style>
            @import url(
                'https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');

            :root {
                --ptg-foreground: #fff;
                --ptg-background: #212121;
            }


            body {
                background: var(--ptg-background);
                color: var(--ptg-foreground);
                font-family: 'Fira Code', monospace;
            }

            pre.ptg {
                font-size: 17px;
                font-family: Menlo,\'DejaVu Sans Mono\',consolas,\'Courier New\', monospace;
            }

        </style>
    </head>
    <body>
    <pre class="ptg">
"""

HTML_FOOTER = """\
    </pre>
    </body>
</html>
"""

_STYLE_TO_CSS = {
    "bold": "font-weight: bold",
    "italic": "font-style: italic",
    "dim": "filter: brightness(70%)",
    "underline": "text-decoration: underline",
    "inverse": "mix-blend-mode: difference",
    "strikethrough": "text-decoration: line-through",
    "overline": "text-decoration: overline",
}


__all__ = ["token_to_css", "to_html"]


def token_to_css(token: Token) -> str:
    """Finds the CSS representation of a token."""

    if token.ttype is TokenType.COLOR:
        color = token.data
        assert isinstance(color, Color)

        style = "color: rgb({}, {}, {});".format(*color.rgb)
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

        for styled in tim.get_styled_plains(line):
            styles = []
            has_link = False
            for token in styled.tokens:
                if token.ttype is TokenType.PLAIN:
                    continue

                if token.ttype is TokenType.LINK:
                    has_link = True
                    yield f"<a href='{token.data}'>"

                css = token_to_css(token)
                if css is not None and css not in styles:
                    styles.append(css)

            index = len(document_styles)
            if styles in document_styles:
                index = document_styles.index(styles)
            else:
                document_styles.append(styles)

            escaped = escape(styled.plain).replace(" ", "&nbsp;")

            value = ";".join(styles) if inline_styles else _get_cls(index)
            prefix = "style" if inline_styles else "class"

            tag = f"<span {prefix}='{value}'>{escaped}</span>"
            tag += "</a>" if has_link else ""
            yield tag

    if isinstance(obj, Widget):
        data = obj.get_lines()

    else:
        data = obj.splitlines()

    document = BASE_HTML

    for line in data:
        for span in _get_spans(line):
            document += span
        document += "<br>"

    if not inline_styles:
        document += "<style>"
        document += "".join(
            f".{_get_cls(i)} " + "{" + f"{';'.join(style)}" + "}"
            for i, style in enumerate(document_styles)
        )
        document += "</style>"

    document += HTML_FOOTER

    return document
