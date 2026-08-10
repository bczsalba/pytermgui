from pytermgui import ColorPicker, pretty, terminal, tim

tim.alias("code", "@black #auto dim")

with terminal.record() as recording:
    tim.print("[italic]Everything[/] you print will be captured!")
    tim.print()
    tim.print(
        "By default, only [code]PTG[/]'s prints functions are affected,"
        + "\nbut by overwriting [code]sys.stdout.write[/] you can capture any Python output."
    )
