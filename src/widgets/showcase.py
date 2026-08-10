import pytermgui as ptg

ptg.boxes.ROUNDED.set_chars_of(ptg.Container)
ptg.Splitter.set_char("separator", " ")

width, height = ptg.get_terminal().size

with ptg.YamlLoader() as loader:
    loader.load(
        """
    config:
        Window:
            styles:
                border: '60'
                corner: '60'

        Container:
            styles:
                border: '96'
                corner: '96'
    """
    )


showcase = ptg.Window(
    ptg.Label("Welcome to [bold !gradient(210)]PyTermGUI[/]!\n"),
    ptg.Splitter(
        ptg.Container(ptg.Label("This is the box on the left")),
        ptg.Container(ptg.Label("This is the box in the middle")),
        ptg.Container(ptg.Label("This is the box on the right")),
    ),
    ptg.Label("\nHere are some interactive elements:"),
    ptg.Container(
        ptg.Splitter(
            ptg.Label("Checkboxes", parent_align=0), ptg.Checkbox(parent_align=2)
        ),
        ptg.Splitter(
            ptg.Label("Buttons", parent_align=0), ptg.Button("Button 1", parent_align=2)
        ),
        ptg.Splitter(ptg.Label("Sliders", parent_align=0), ptg.Slider(parent_align=2)),
        relative_width=2 / 3,
    ),
    width=width,
    box="DOUBLE",
)

with ptg.WindowManager() as manager:
    manager.layout.add_slot()
    manager.add(showcase)
