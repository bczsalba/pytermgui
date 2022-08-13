from pytermgui import pretty, Container, boxes

container = Container(box="EMPTY")

for name in [name for name in dir(boxes) if name.isupper()]:
    box = getattr(boxes, name)

    container += Container(
        f"[primary]{name}",
        box=box,
    )

&container.static_width = 70
&termage.fit(container)
for line in container.get_lines():
    print(line)
