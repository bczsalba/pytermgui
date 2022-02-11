#!/usr/bin/env python3


from string import ascii_lowercase

header = """\
\"\"\"
pytermgui.keys
--------------
author: generate_keys.py :)


This file is generated to house the Keys class.
\"\"\"

class Keys:
    UP = "\
"""


def main() -> None:
    lines = []

    for i, letter in enumerate(ascii_lowercase):
        lines.append(
            f"    CTRL_{letter.upper()} = \"{chr(i+1).encode('unicode_escape').decode('utf-8')}\""
        )

    print(header + "\n".join(lines))


if __name__ == "__main__":
    main()
