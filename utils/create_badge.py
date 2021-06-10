#!/usr/bin/env python3

from subprocess import check_output, DEVNULL
from argparse import ArgumentParser

COLORS = {
    "brightgreen": "#4c1",
    "green": "#97CA00",
    "yellow": "#dfb317",
    "yellowgreen": "#a4a61d",
    "orange": "#fe7d37",
    "red": "#e05d44",
    "bloodred": "#ff0000",
    "blue": "#007ec6",
    "gray": "#555",
    "lightgray": "#9f9f9f",
}

TEMPLATE = '<svg xmlns="http://www.w3.org/2000/svg" width="125" height="20"><linearGradient id="a" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><rect rx="3" width="125" height="20" fill="#555"/><rect ry="3" x="85" width="50" height="20" fill="{color}"/><path fill="{color}" d="M85 0h4v50h-4z"/><rect rx="3" width="125" height="20" fill="url(#a)"/><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="41" y="15" fill="#010101" fill-opacity=".3">pylint quality</text><text x="41" y="14">pylint quality</text><text x="105" y="15" fill="#010101" fill-opacity=".3">{score}</text><text x="105" y="14">{score}</text></g></svg>'


def get_color(score: float) -> str:
    """Get color from COLORS dict"""

    if score > 9:
        return COLORS["brightgreen"]

    if score > 8:
        return COLORS["green"]

    if score > 7.5:
        return COLORS["yellowgreen"]

    if score > 6.6:
        return COLORS["yellow"]

    if score > 5.0:
        return COLORS["orange"]

    if score > 0.00:
        return COLORS["red"]


def main(name: str = "assets/quality.svg") -> float:
    """Create an SVG showing the code quality"""

    output = check_output("make lint", shell=True).decode("utf-8")
    start = output.find("Your code has been rated at ")
    assert not start == -1

    start += len("Your code has been rated at ")
    end = start + output[start:].find("/")
    score = output[start:end]

    color = get_color(float(score))

    with open(name, "w") as score_file:
        score_file.write(TEMPLATE.format(score=score, color=color))

    return score
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "name", 
        nargs="?",
        default="assets/quality.svg",
        type=str,
        help="name of the badge file"
    )

    args = parser.parse_args()

    score = main(args.name)
    print(f"Created badge for score {score} at {args.name}!")
