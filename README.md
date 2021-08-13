<!-- TODO: these colors could be randomly generated -->
![title](https://github.com/bczsalba/pytermgui/raw/master/assets/title.png)

> A simple yet powerful TUI framework for your Python (3.7+) applications
```
pip3 install pytermgui
```

[![PyPI version](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/version.svg)](https://pypi.org/project/pytermgui)
[![Pylint quality](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/quality.svg)](https://github.com/bczsalba/pytermgui/blob/master/utils/create_badge.py)


Core principles
---------------

<!-- Look into rewording this -->
`PTG` was written with some core ideas in mind, such as:
- Pythonic syntax
- Flexible systems
- High quality code
- Extensibility by design

What we provide
---------------

- Terminal mouse support
- A [program](https://www.reddit.com/link/p3b6ou/video/kkfhn20of0h71/player?utm_source=reddit&utm_medium=usertext&utm_name=Python&utm_content=t3_p3b6ou) with helpful [CLI applications](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/cmd.py) (`ptg --help`)
- A fully flegded [WindowManager](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/window_manager.py) in the terminal
- A cross-platform [getch](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/input.py) function with key translations
- An [interface](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/ansi_interface.py) to most terminal functionality
- A custom markup language with definable tags & macros inspired by [Rich](https://github.com/willmcgugan/rich/tree/master/rich)
- [Tokenizer & optimizer](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/parser.py) methods for ANSI-sequence strings
- A robust, extensible and customizable [Widget](https://github.com/bczsalba/pytermgui/blob/master/pytermgui/widgets) class
- Helpful [example files](https://github.com/bczsalba/pytermgui/tree/master/examples) covering most of the library


An example to get started with
------------------------------
```python
# Note: This example uses the auto-conversion syntax. 
#       For more info, check out `help(pytermgui.auto)`.

import sys
from pytermgui import WindowManager, Window

manager = WindowManager()
window = (
    Window(min_width=50)
    + "[210 bold]My first Window!"
    + ""
    + "[157]Try resizing the window by dragging the right border"
    + "[157]Or drag the top border to move the window"
    + "[193 bold]Alt-Tab[/bold 157] cycles windows"
    + "[193 bold]CTRL_C[/bold 157] exits the program"
    + ""
    + ["New window", lambda *_: manager.add(window.copy().center())]
    + ["Close current", lambda _, button: manager.close(button.parent)]
    + ["Exit program", lambda *_: sys.exit(0)]
)

manager.add(window)
manager.run()

```

<!-- TODO: Figure out a better quality for this -->
![readme wm gif](https://github.com/bczsalba/pytermgui/raw/master/assets/readme_wm.gif)

Some screenshots
----------------

[![hello_world](https://github.com/bczsalba/pytermgui/raw/master/assets/hello_world.png)](https://github.com/bczsalba/pytermgui/blob/master/examples/hello_world.py)
[![bezo calc](https://github.com/bczsalba/pytermgui/raw/master/assets/bezocalc.png)](https://github.com/bczsalba/pytermgui/blob/master/examples/bezocalc.py)

Documentation
-------------

As the project is in its infancy, dedicated documentation is not yet available. 

If you are interested in help about anything the module provides, you can read its docstring:
```bash
python3 -c "help(pytermgui.<name>)"
```

However, proper documentation is coming once the API is stable.
