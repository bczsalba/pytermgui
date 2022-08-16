from pytermgui import Container, Label, pretty

container = Container(
    Label("This is the left", parent_align=0),
    Label("This is the center", parent_align=1),
    Label("This is the right", parent_align=2),
)

&container.static_width = 60
&termage.fit(container)
for line in container.get_lines():
    print(line)
