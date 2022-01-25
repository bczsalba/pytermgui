import requests
from subprocess import check_output


def get_score(command: str) -> float:
    """Get pylint score"""

    output = check_output(command, shell=True).decode("utf-8")
    start = output.find("Your code has been rated at ")
    if start == -1:
        raise ValueError(f'Could not find quality score in "{output.rstrip()}".')

    start += len("Your code has been rated at ")
    end = start + output[start:].find("/")
    score = float(output[start:end])

    return score


def get_color(score: float) -> str:
    """Get color for shield"""

    if score < 6:
        return "critical"

    elif score < 8:
        return "orange"

    elif score < 9:
        return "yellow"

    elif score < 9.5:
        return "yellowgreen"

    else:
        return "brightgreen"


def create_link(label: str, score: float) -> str:
    """Create link using shields.io"""

    label = label.replace(" ", "_")
    color = get_color(score)
    return f"https://img.shields.io/badge/{label}-{score}-{color}"


def write_quality_badge(command: str, output_file: str) -> None:
    """Write badge for code quality"""

    score = get_score("make lint")
    link = create_link("code quality", score)

    with open(output_file, "wb") as output:
        data = requests.get(link).content
        output.write(data)


def write_version_badge(output_file: str) -> None:
    """Write badge for version badge"""

    from pytermgui import __version__ as version

    link = f"https://img.shields.io/badge/pypi_package-{version}-bright_green"

    with open(output_file, "wb") as output:
        data = requests.get(link).content
        output.write(data)


def main() -> None:
    """Main method"""

    write_quality_badge("make lint", "assets/badges/quality.svg")
    write_version_badge("assets/badges/version.svg")


if __name__ == "__main__":
    main()
