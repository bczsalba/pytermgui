from pytermgui import Button, Container, pretty, tim

template = "[@primary #auto] {first} [@surface-1 #auto] {second} "


def split_style(_: int, item: str) -> str:
    if "<SPLIT>" not in item:
        return item

    first, second = item.split("<SPLIT>")
    return tim.parse(template.format(first=first, second=second))


Button.styles.label = split_style
Button.set_char("delimiter", [""] * 2)
my_button = Button("Hey<SPLIT>There")

pretty.print(my_button)
