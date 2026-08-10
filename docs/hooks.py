"""MkDocs build hooks."""

import os

from pytermgui import ColorSystem, terminal


def on_config(config):
    """Use deterministic true-color rendering for generated documentation images."""

    os.environ["PTG_COLOR_SYSTEM"] = "TRUE"
    terminal.forced_colorsystem = ColorSystem.TRUE

    return config
