from pytermgui import Label, Container, boxes

art = """\
[bold 157] ____      [60] _____                  [210]  ____ _   _ ___ [/]
[bold 157]|  _ \ _   [60]|_   _|__ _ __ _ __ ___ [210] / ___| | | |_ _|[/]
[bold 157]| |_) | | | |[60]| |/ _ \ '__| '_ ` _ .[210]| |  _| | | || | [/]
[bold 157]|  __/| |_| |[60]| |  __/ |  | | | | | [210]| |_| | |_| || | [/]
[bold 157]|_|    \__, |[60]|_|\___|_|  |_| |_| |_|[210]\____|\___/|___|[/]
 ====== [bold 157]|___/[/fg] ======================================= [/]
"""

Container.set_char("border", [""] * 4)
root = Container()
for line in art.splitlines():
    root += Label(line)

root.center()
root.print()
