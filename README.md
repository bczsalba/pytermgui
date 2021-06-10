<!-- Todo: these colors could be randomly generated -->
![title](https://github.com/bczsalba/pytermgui/raw/master/assets/title.png)

> A simple yet powerful TUI framework for your Python (3.9+) applications
```
pip3 install pytermgui
```
[![PyPI version](https://badge.fury.io/py/pytermgui.svg)](https://badge.fury.io/py/pytermgui)

Core principles
---------------

<!-- Look into rewording this one -->
`PTG` was written with some core ideas in mind, such as:
- Pythonic syntax
- Flexible systems
- Extensibility by design
- Readable, reproducible code

```python
from pytermgui import Container, Label
root = Container() + Label("Clean code is [bold]cool[/bold]!")
root.print()
```

What we provide
---------------

- A cross-platform [getch](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/input.py) function with key translations
- An [interface](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/ansi_interface.py) to most terminal functionality
- A custom markup language inspired by [Rich](https://github.com/willmcgugan/rich/tree/master/rich)
- [Tokenizer & optimizer](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/parser.py) methods for ANSI-sequence strings
- A robust, extensible and customizable [Widget](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/widgets) class
- helpful [CLI tools](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/cmd.py) (`ptg --help`)
- Helpful [example files](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/cmd.py) covering most of the library

```python
>>> from pytermgui import optimize_ansi
>>> original = "\x1b[0m\x1b[0m\x1b[0m\x1b[38;5;141m\x1b[38;5;65m\x1b[0m\x1b[1mSee the difference?\x1b[0m"
>>> optimize_ansi(original)

'\x1b[1mSee the difference?\x1b[0m'
```

Example to get started with
---------------------------
```python
from pytermgui import Container, Label, InputField, MarkupFormatter, getch, alt_buffer, boxes

border_corner_markup = MarkupFormatter("[60 bold]{item}")
Container.set_style('border', border_corner_markup)
Container.set_style('corner', border_corner_markup)
boxes.SINGLE.set_chars_of(Container)

root = Container()
root.forced_width = 70

boxes.DOUBLE_TOP.set_chars_of(root)
root += Label("[210 bold] Welcome to [italic]PyTermGUI![/]", align=Label.ALIGN_LEFT)
root += Label()

field = InputField("Enter something!")
field.set_style('value', MarkupFormatter("[italic 72]{item}"))
field.set_style('cursor', MarkupFormatter("[@72]{item}"))

field_container = Container(vert_align=Container.VERT_ALIGN_TOP) + field
field_container.forced_height = 7
root += field_container

root += Label("[245 italic]> Press CTRL_C to exit...", align=Label.ALIGN_RIGHT)

root.focus()

with alt_buffer(cursor=False):
    root.center()
    root.print()

    while True:
        key = getch(interrupts=False)

        if key == chr(3):
            break

        field.send(key)
        root.center()
        root.print()

print('Goodbye!')
```
[![readme](https://github.com/bczsalba/pytermgui/raw/master/assets/readme_image.png)](#example-to-get-started-with)

Some screenshots
----------------

[![hello_world](https://github.com/bczsalba/pytermgui/raw/master/assets/hello_world.png)](https://github.com/bczsalba/pytermgui/blob/master/examples/hello_world.py)
[![bezo calc](https://github.com/bczsalba/pytermgui/raw/master/assets/bezocalc.png)](https://github.com/bczsalba/pytermgui/blob/master/examples/bezocalc.py)

Why the ~~long nose~~ version requirement?
------------------------------------------

`PyTermGUI` makes heavy use of the typing module, which in Python 3.9 saw the inclusion of container parameterizing, allowing the use of `list[str]` instead of `List[str]`.

The previous method is now deprecated, and there isn't any nice way of supporting both forever. As such, the use of the new syntax makes Python 3.8x and lower raise `SyntaxError`.

There isn't really much to help this issue, and its good practice to stay on the most recent release regardless.

```python
from pytermgui import Container, Prompt, Label, boxes
boxes.EMPTY_VERTICAL.set_chars_of(Container)

def dict_to_container(data: dict[str, str]) -> Container:
    """Create container from a dict"""

    root = Container()
    for key, value in data.items():
        root += Prompt(key, value)

    return root

root = Container()
root += Label("[246 italic bold] a guide on the python version you should use")

root += dict_to_container({
    "[157]python >3.9[/]": "[157]good[/]",
    "[210]python <3.8[/]": "[210]bad[/]",
})
root.print()
```

![guide](https://github.com/bczsalba/pytermgui/raw/master/assets/version_guide.png)

Documentation
-------------

As the project is in its infancy, dedicated documentation is not yet available. 

If you are interested in help about anything the module provides, you can read its docstring:
```bash
python3 -c "help(<name>)"
```

However, proper documentation is coming soon.
