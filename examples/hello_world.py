"""
pytermgui/examples/hello_world.py
---------------------------------
author: bczsalba


This is a relatively simple program that creates a root Container
showcasing various functionalities of the module.
"""

from random import randint
from pytermgui import (
    Container,
    Splitter,
    Prompt,
    Label,
    MarkupFormatter,
    ListView,
    boxes,
)


def random_255() -> int:
    """Get random 8-bit color"""

    return str(randint(0, 255))


def random_rgb() -> tuple[int, int, int]:
    """Get random rgb color"""

    return ";".join(random_255() for _ in range(3))


def random_hex() -> str:
    """Get random hex color"""

    rgb = tuple(int(color) for color in random_rgb().split(";"))
    return "#" + "%02x%02x%02x" % rgb


# set up styles
border_markup = MarkupFormatter("[bold 60]{item}")
Container.set_style("border", border_markup)
Container.set_style("corner", border_markup)
Splitter.set_style("separator", border_markup)
Splitter.set_char("separator", boxes.SINGLE.borders[0])
boxes.SINGLE.set_chars_of(Container)

# create root Container
root = Container(width=25) + {"[222 bold]hello": "[72]world"}
boxes.DOUBLE_TOP.set_chars_of(root)

# create inner Container, add elements to it
inner = (
    Container()
    + "This is an inner [italic bold 24]label"
    + "All [208]widgets[/fg] support [bold @61 141]markup"
    + "There is also support for [green bold]named [red bold]colors."
)

# add inner to root
root += inner


# create style container
style_tags = [
    "/",
    "bold",
    "dim",
    "italic",
    "underline",
    "blink",
    "blink2",
    "inverse",
    "invisible",
    "strikethrough",
    "",
]

styles = Container()
styles.set_char("border", [""] * 4)
styles.set_char("corner", [""] * 4)

for tag in style_tags:
    if tag == "":
        styles += Label()
    else:
        styles += Label(f"[{tag}]{tag}")


# create color container
color_tags = [
    f"[{random_255()}]0-255",
    f"[{random_hex()}]#rrbbgg",
    f"[{random_rgb()}]rrr;bbb;ggg",
    "",
    f"[@{random_255()}]@0-255",
    f"[@{random_hex()}]@#rrbbgg",
    f"[@{random_rgb()}]@rrr;bbb;ggg",
    "",
    "[210]/fg",
    "[210]/bg",
    "[210]/{tag}",
]

colors = Container()
colors.set_char("border", [""] * 4)
colors.set_char("corner", [""] * 4)

for tag in color_tags:
    colors += Label(tag)


# creates features Container
features = Container() + (Splitter() + styles + colors)


# set up features' corners
corners = features.get_char("corner").copy()
corners[0] += " tags "
corners[1] = " colors " + corners[1]
features.set_char("corner", corners)

# add features to root
root += features

# center object & print it
root.center()
root.print()
