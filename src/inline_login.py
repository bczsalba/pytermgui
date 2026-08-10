import pytermgui as ptg

ptg.tim.print("[bold 109]lapis: [110]docs [109]*[/] python3 inline_login.py")

prompt = ptg.Container(
    "[secondary]User information",
    "",
    ptg.InputField("Balazs Cene", prompt="Name: "),
    ptg.InputField("***********", prompt="Password: "),
    "",
    [("Stay logged in", "One time")],
)

for line in prompt.get_lines():
    termage.terminal.print(line)
