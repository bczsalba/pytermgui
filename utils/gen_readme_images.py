import os
from importlib import reload
from pathlib import Path

from termage import termage

project_root = Path(__file__).parent.parent.resolve()
script_dir = project_root / "utils" / "readme_scripts"
output_dir = project_root / "assets" / "readme"

for script in script_dir.iterdir():
    with open(script, "r") as file:
        code = file.read()

    termage(
        code,
        title=str(script.relative_to(project_root)),
        out=(output_dir / script.stem).with_suffix(".svg"),
        bg="#212121",
    )

    print(f"Generated SVG for {script}.")
