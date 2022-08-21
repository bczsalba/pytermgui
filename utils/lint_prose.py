import re
from pathlib import Path

import proselint
from proselint.config import default as DEFAULT_CONFIG

from pytermgui import break_line, terminal, tim

RE_ADMONITION_HEADER = re.compile(r'([\!\?]{3}) \w+(?: ".*?")?')
RE_QUOTE = re.compile(r'"(.*?)"')
RE_CODEBLOCK = re.compile(r"(```.*?\n[\s\S]*?\n?```)")

docs = Path("docs")

ignored = [
    "leonard.exclamation.30ppm",
    "leonard.exclamation.multiple",
    "cliches.write_good",
]

for path in docs.glob("**/*.md"):
    with open(path, "r") as f:
        content = f.read()

    # Remove non-regex compatible escapes (mostly ANSI SGR)
    content = content.replace(r"\x", "").replace("...", "…")
    # Remove admonition headers
    content = RE_ADMONITION_HEADER.sub("---------------", content)
    # Remove codeblocks completely
    content = RE_CODEBLOCK.sub(lambda m: m[1].count("\n") * "-+-+-+-+-\n", content)
    # Change quote characters
    content = RE_QUOTE.sub(lambda m: f"“{m[1]}”", content)

    result = proselint.tools.lint(content, config=DEFAULT_CONFIG)
    result = list(filter(lambda item: item[0] not in ignored, result))

    if result != []:
        tim.print(f"[primary+2]{path}:")

        for check, message, row, col, *_ in result:
            row += 1

            tim.print(
                f"  [~file://{path.absolute()}]{path.name}[/]:"
                + f"{row}:{col} [warning]{check}[/]:"
            )
            for line in break_line(message, terminal.width * 2 / 3):
                tim.print("    " + f"[surface+2]{line}")

            print()
