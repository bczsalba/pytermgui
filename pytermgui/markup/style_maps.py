"""Dictionaries that define the terminal's styles & their unsetters."""

STYLES = {
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
    "blink": "5",
    "blink2": "6",
    "inverse": "7",
    "invisible": "8",
    "strikethrough": "9",
    "overline": "53",
}

REVERSE_STYLES = {value: key for key, value in STYLES.items()}

CLEARERS = {
    "/": "0",
    "/bold": "22",
    "/dim": "22",
    "/italic": "23",
    "/underline": "24",
    "/blink": "25",
    "/blink2": "26",
    "/inverse": "27",
    "/invisible": "28",
    "/strikethrough": "29",
    "/fg": "39",
    "/bg": "49",
    "/overline": "54",
}

REVERSE_CLEARERS = {value: key for key, value in CLEARERS.items()}
