from termage import termage

BACKGROUND = "#212121"
PALETTE_WIDTH = "91"
PALETTE_HEIGHT = "44"

SCRIPT = """\
from pytermgui import Palette
Palette(primary="#4e754a", strategy="{strategy}").print()"""

termage(
    SCRIPT.format(strategy="triadic"),
    title="triadic strategy",
    width=PALETTE_WIDTH,
    height=PALETTE_HEIGHT,
    bg=BACKGROUND,
    out="docs/assets/triadic.svg",
)

termage(
    SCRIPT.format(strategy="analogous"),
    title="analogous strategy",
    width=PALETTE_WIDTH,
    height=PALETTE_HEIGHT,
    bg=BACKGROUND,
    out="docs/assets/analogous.svg",
)
