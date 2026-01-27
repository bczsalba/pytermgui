#!/usr/bin/env python3
"""Run: python examples/wcwidth_demo.py

Demonstrates break_line() issues with wide characters and grapheme clusters.
"""
import pytermgui as ptg

CJK = "中文字符"
FAMILY = "\U0001F468\u200D\U0001F469\u200D\U0001F467"
FLAG = "\U0001F1E8\U0001F1E6"  # Canada

# Additional grapheme examples from wcwidth tests
WAVE_SKIN = "\U0001F44B\U0001F3FB"  # Waving hand + skin tone modifier
HEART_VS16 = "\u2764\uFE0F"  # Heart + variation selector-16
CAFE = "cafe\u0301"  # café with combining acute accent
WOMAN_TECH = "\U0001f469\U0001f3fb\u200d\U0001f4bb"  # Woman technologist (ZWJ)
KISS = "\U0001F9D1\U0001F3FB\u200d\u2764\uFE0F\u200d\U0001F48B\u200d\U0001F9D1\U0001F3FD"  # Kiss

# ANSI escape codes for color testing
RST = "\x1b[0m"
BOLD = "\x1b[1m"
ITALIC = "\x1b[3m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
ORANGE_256 = "\x1b[38;5;208m"
PURPLE_256 = "\x1b[38;5;129m"
CYAN_RGB = "\x1b[38;2;0;255;255m"
PINK_RGB = "\x1b[38;2;255;105;180m"

# Big word with 24-bit RGB gradient
CHOOCHOO = (
    "\x1b[38;2;255;0;0mc"
    "\x1b[38;2;255;127;0mh"
    "\x1b[38;2;255;255;0mo"
    "\x1b[38;2;0;255;0mo"
    "\x1b[38;2;0;255;127mc"
    "\x1b[38;2;0;255;255mh"
    "\x1b[38;2;0;127;255mo"
    "\x1b[38;2;0;0;255mo"
    "\x1b[38;2;127;0;255mp"
    "\x1b[38;2;255;0;255mo"
    "\x1b[38;2;255;0;127mn"
    "\x1b[38;2;255;0;0my"
    "\x1b[38;2;255;127;0me"
    "\x1b[38;2;255;255;0mx"
    "\x1b[38;2;0;255;0mp"
    "\x1b[38;2;0;255;127mr"
    "\x1b[38;2;0;255;255me"
    "\x1b[38;2;0;127;255ms"
    "\x1b[38;2;0;0;255ms"
    "\x1b[0m"
)

ptg.WindowManager.autorun = False

# Track adjustable containers and current width
current_width = 19
column_width = 25
adjustable_containers = []
column_containers = []
main_window = None


def adjust_width(delta):
    """Adjust width of all tracked containers."""
    global current_width, column_width, main_window
    new_width = max(6, min(30, current_width + delta))
    if new_width != current_width:
        current_width = new_width
        column_width = column_width + delta
        for container in adjustable_containers:
            container.static_width = current_width
        for column in column_containers:
            column.static_width = column_width
        if main_window is not None:
            main_window.width = main_window.width + delta * 4
        width_label.value = f"[dim]Width: {current_width}  |  ←/→ adjust  |  Ctrl+C exit[/]"


with ptg.WindowManager() as manager:
    manager.mouse_enabled = False

    # Bind arrow keys for width adjustment
    manager.bind(ptg.keys.LEFT, lambda *_: adjust_width(-1), "Decrease width")
    manager.bind(ptg.keys.RIGHT, lambda *_: adjust_width(1), "Increase width")

    # Create containers and track the adjustable ones
    sgr_box = ptg.Container(ptg.Label(f"{BOLD}bold{RST} {ITALIC}italic{RST}"),
                            static_width=current_width)
    colors_box = ptg.Container(ptg.Label(f"{RED}red{RST} {GREEN}green{RST}"),
                               static_width=current_width)
    c256_box = ptg.Container(ptg.Label(f"{ORANGE_256}orange{RST} {PURPLE_256}purple{RST}"),
                             static_width=current_width)
    rgb_box = ptg.Container(ptg.Label(f"{CYAN_RGB}cyan{RST} {PINK_RGB}pink{RST}"),
                            static_width=current_width)

    wrap_box = ptg.Container(ptg.Label("The quick-brown-fox"), static_width=current_width)
    cjk_box = ptg.Container(ptg.Label(CJK + CJK), static_width=current_width)
    family_box = ptg.Container(ptg.Label(f"Hi{FAMILY}!"), static_width=current_width)
    flag_box = ptg.Container(ptg.Label(f"{FLAG}Canada"), static_width=current_width)

    combine_box = ptg.Container(ptg.Label(f"A {CAFE}!"), static_width=current_width)
    skin_box = ptg.Container(ptg.Label(f"Hi{WAVE_SKIN}!"), static_width=current_width)
    heart_box = ptg.Container(ptg.Label(f"I{HEART_VS16}U"), static_width=current_width)
    tech_box = ptg.Container(ptg.Label(f"{WOMAN_TECH}codes"), static_width=current_width)
    lorem_box = ptg.Container(ptg.Label("Lorem ipsum dolor sit"), static_width=current_width)
    choochoo_box = ptg.Container(ptg.Label(CHOOCHOO), static_width=current_width)

    adjustable_containers = [
        sgr_box, colors_box, c256_box, rgb_box,
        wrap_box, cjk_box, family_box, flag_box,
        combine_box, skin_box, heart_box, tech_box,
        lorem_box, choochoo_box,
    ]

    left = ptg.Container(
        ptg.Label("[bold]ANSI Sequences[/]"),
        "",
        ptg.Label("SGR:"),
        sgr_box,
        "",
        ptg.Label("Colors:"),
        colors_box,
        "",
        ptg.Label("256-color:"),
        c256_box,
        "",
        ptg.Label("24-bit RGB:"),
        rgb_box,
        static_width=column_width,
    )

    middle = ptg.Container(
        ptg.Label("[bold]Width & Graphemes[/]"),
        "",
        ptg.Label("Word wrap:"),
        wrap_box,
        "",
        ptg.Label("CJK (2-cell):"),
        cjk_box,
        "",
        ptg.Label("Family ZWJ:"),
        family_box,
        "",
        ptg.Label("Flag:"),
        flag_box,
        static_width=column_width,
    )

    right = ptg.Container(
        ptg.Label("[bold]Grapheme Clusters[/]"),
        "",
        ptg.Label("Combining:"),
        combine_box,
        "",
        ptg.Label("Skin tone:"),
        skin_box,
        "",
        ptg.Label("VS-16 heart:"),
        heart_box,
        "",
        ptg.Label("Woman tech:"),
        tech_box,
        static_width=column_width,
    )

    far_right = ptg.Container(
        ptg.Label("[bold]Long Text[/]"),
        "",
        ptg.Label("Lorem ipsum:"),
        lorem_box,
        "",
        ptg.Label("RGB gradient:"),
        choochoo_box,
        static_width=column_width,
    )

    column_containers.extend([left, middle, right, far_right])

    width_label = ptg.Label(f"[dim]Width: {current_width}  |  ←/→ adjust  |  Ctrl+C exit[/]")

    main_window = ptg.Window(
        ptg.Label("[bold]break_line() Demo[/]"),
        "",
        ptg.Splitter(left, middle, right, far_right),
        "",
        width_label,
        width=113,
    )
    manager.add(main_window)
    manager.run()
