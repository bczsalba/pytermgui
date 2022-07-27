import os
from importlib import reload
from pathlib import Path

from termage.__main__ import main as termage

import pytermgui as ptg


def generate_image(**kwargs: str) -> None:
    args = ["--bg", "#212121"]

    for key, value in kwargs.items():
        args.extend((f"--{key}", str(value)))

    termage(args)


project_root = Path(__file__).parent.parent.resolve()
script_dir = project_root / "utils" / "readme_scripts"
output_dir = project_root / "assets" / "readme"

for script in script_dir.iterdir():
    generate_image(
        file=script,
        title=str(script.relative_to(project_root)),
        out=str(output_dir / script.stem) + ".svg",
    )

    print(f"Generated SVG for {script}.")
