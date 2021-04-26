from . import (
    set_style,
    color,
    gradient,
    bold,
    italic,
    strikethrough,
    underline,
    highlight,
    get_gradient,
)


def random():
    """ Style using randomly generated colors, gradient indicating object depth """

    from random import randint

    accent1 = randint(17, 230)
    accent2 = randint(17, 230)
    set_style("prompt_long_highlight", lambda depth, item: highlight(item, accent1))
    set_style("prompt_short_highlight", lambda depth, item: highlight(item, accent1))
    set_style("prompt_delimiter_chars", lambda: None)
    set_style(
        "container_border",
        lambda depth, item: bold(color(item, get_gradient(accent2)[depth])),
    )
    set_style("label_value", lambda depth, item: bold(color(item, accent1)))

    return accent1, accent2


def draculite():
    """ Style used by default on teahaz, lightly inspired by Dracula """

    set_style("label_value", lambda depth, item: bold(color(item.upper(), 210)))
    set_style("prompt_label", lambda depth, item: color(item, 248))
    set_style("prompt_value", lambda depth, item: color(item, 72))
    set_style("inputfield_value", lambda depth, item: color(item, 72))
    set_style("inputfield_highlight", lambda depth, item: highlight(item, 72))
    set_style(
        "container_border",
        lambda depth, item: bold(color(item, get_gradient(60)[depth])),
    )
    set_style("prompt_short_highlight", lambda depth, item: highlight(item, 72))
    set_style("prompt_long_highlight", lambda depth, item: highlight(item, 72))
    set_style("prompt_delimiter_chars", lambda: "<>")
