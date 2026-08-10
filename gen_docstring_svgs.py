from mkdocs_gen_files import open as virtopen
from termage import termage

BACKGROUND = "#212121"
PALETTE_WIDTH = 91
PALETTE_HEIGHT = 44

SCRIPT = """from pytermgui import Palette
Palette(primary="#4e754a", strategy="{strategy}").print()"""

# We use gen_file's virtual openers to avoid tripping livereload
with virtopen("assets/triadic.svg", "w") as virtfile:
    virtfile.write(
        termage(
            SCRIPT.format(strategy="triadic"),
            title="triadic strategy",
            width=PALETTE_WIDTH,
            height=PALETTE_HEIGHT,
            background=BACKGROUND,
        )
    )

with virtopen("assets/analogous.svg", "w") as virtfile:
    virtfile.write(
        termage(
            SCRIPT.format(strategy="analogous"),
            title="analogous strategy",
            width=PALETTE_WIDTH,
            height=PALETTE_HEIGHT,
            background=BACKGROUND,
        )
    )
