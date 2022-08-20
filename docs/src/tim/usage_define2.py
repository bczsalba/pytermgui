from pytermgui import tim

LANGUAGE = "en"

TRANSLATIONS = {
    "welcome": {
        "en": "Welcome to the documentation",
        "hu": "Üdv a dokumentációban",
    }
}


def macro_lang(key: str) -> str:
    translation = TRANSLATIONS.get(key)

    if translation is None:
        return key

    return translation[LANGUAGE]


tim.define("!lang", macro_lang)

for LANGUAGE in ["en", "hu"]:
    tim.clear_cache()

    tim.print(f"[bold]LANGUAGE: [/ 157]{LANGUAGE!r}")
    tim.print("--> [!lang]welcome[/!lang]")
    tim.print()
