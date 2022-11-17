from pytermgui import tim
from pytermgui.color_info import CSS_COLORS

colors = list(CSS_COLORS.keys())

COL_COUNT = 3
COL_WIDTH = 20
TOTAL_WIDTH = COL_COUNT * COL_WIDTH


buff = ""
OFFSET = len(colors) // COL_COUNT


def color_at_index(column: int, index: int) -> str:
    color = colors[index]
    aligner = "<" if count == 0 else (">" if count == len(indices) - 1 else "^")

    return f"[{color}]{color:{aligner}{COL_WIDTH}}[/]"


def get_offset_indices(i: int) -> filter:
    return tuple(
        filter(
            lambda x: x < len(colors),
            (i + OFFSET * column_index for column_index in range(COL_COUNT)),
        )
    )


i = 0
visited = []

while True:
    indices = get_offset_indices(i)

    if len(indices) == 0 or indices[-1] == len(colors):
        break

    if indices[-1] // OFFSET == COL_COUNT and buff.split("\n")[-1] == "":
        buff += (TOTAL_WIDTH - COL_WIDTH) * " "

    for count, index in enumerate(indices):
        if index in visited:
            continue

        visited.append(index)
        buff += color_at_index(count, index)

    buff += "\n"
    i += 1

tim.print(buff)
