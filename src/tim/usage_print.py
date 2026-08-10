from pytermgui import tim

tim.define("!reverse", lambda text: text[::-1])

tim.print(
    "[slategrey italic]So much formatting, [!reverse !upper]where[/!] does it all fit?"
)
