from pytermgui import tim

LANG = "en"


def toggle_lang() -> None:
    global LANG

    LANG = "hu" if LANG == "en" else "en"
    tim.print(f"LANGUAGE: [bold lime]{LANG}")


LOCALIZATION_DATA = {
    "welcome-long": {
        "en": "Welcome to the docs!",
        "hu": "Üdv a dokumentációban!",
    },
    "settings": {
        "en": "Settings",
        "hu": "Beállítások",
    },
}


def macro_lang(ident: str) -> str:
    return LOCALIZATION_DATA[ident][LANG]


tim.define("!lang", macro_lang)

for _ in range(2):
    toggle_lang()
    tim.clear_cache()

    tim.print("[!lang italic]welcome-long")
    tim.print("[!lang]settings")
    tim.print()
