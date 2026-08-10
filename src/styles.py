from pytermgui import markup, tim

buff = ""

for style in markup.style_maps.STYLES:
    buff += "[{style}]{style}[/]\n"

tim.print(buff)
