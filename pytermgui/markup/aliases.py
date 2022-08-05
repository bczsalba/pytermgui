"""All PTG-builtin TIM aliases."""

from typing import Any

MarkupLanguage = Any  # pylint: disable=invalid-name

CODE_GROUP = {
    "code.str": "142",
    "code.multiline_str": "142",
    "code.keyword": "203",
    "code.none": "167",
    "code.global": "214",
    "code.number": "175",
    "code.identifier": "109",
    "code.name": "214",
    "code.comment": "240 italic",
    "code.builtin": "214",
    "code.file": "109",
    "code.symbol": "code.file",
}


DEFAULT_ALIASES = {**CODE_GROUP, **{"background": ""}}


def apply_default_aliases(lang: MarkupLanguage) -> None:
    """Applies all aliases within `DEFAULT_ALIASES`.

    Args:
        lang: The `MarkupLanguage` instance all aliases will be
            applied to.
    """

    lang.alias_multiple(**DEFAULT_ALIASES)
