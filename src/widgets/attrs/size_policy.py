from pytermgui import Container, SizePolicy, pretty

container = Container(
    Container("I fill the space"),
    Container("I take up 70%", relative_width=0.7),
    Container("I take up exactly\n31 characters", static_width=31),
)


&container.static_width = 70
&termage.fit(container)
print("\n".join(container.get_lines()))
