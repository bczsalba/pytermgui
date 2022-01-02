<!-- TODO: these colors could be randomly generated -->
![title](https://github.com/bczsalba/pytermgui/raw/master/assets/title.png)

> A simple yet powerful TUI framework for your Python (3.7+) applications
```
pip3 install pytermgui
```

[![PyPI version](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/version.svg)](https://pypi.org/project/pytermgui)
[![Pylint quality](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/quality.svg)](https://github.com/bczsalba/pytermgui/blob/master/utils/create_badge.py)


Batteries included or bare-metal. It's your choice.
---------------------------------------------------

pytermgui has both higher and lower level interfaces. If you're only here for the terminal APIs, `ansi_interface` will be your friend.


Adapting to your needs
----------------------

Here are just a couple of ways to define the same widget structure:

**Using the basic class structure**

```python3
# -- demo.py --
import pytermgui as ptg

demo = ptg.Window(
   ptg.Label("[210 bold]Hello world!"),
   ptg.Label(),
   ptg.InputField(prompt="Who are you?")
   ptg.Label(),
   ptg.Button("Submit!")
)
```

**Using data-pattern conversion**

```python3
# -- demo.py --
import pytermgui as ptg

demo = (
    ptg.Window()
    + "[210 bold]Hello world!"
    + ""
    + ptg.InputField(prompt="Who are you?")
    + ""
    + ["Submit!"]
)
```


**Using YAML**

```yaml
# -- demo.yaml --
widgets:
    demo:
        type: Window
        widgets:
          - Label:
                value: "[210 bold]Hello world!"
          - Label: {}

          - InputField:
                prompt: Who are you?
          - Label: {}

          - Button:
                label: Submit!
```

None of these is better than any other, it is all up to individual taste. We don't force you to do
what *we* want, rather encourage you to morph the library around your needs.

By the way, this is what the created `Window` looks like. Nifty, huh?

<p align="center">
    <img src="assets/demos/versatility.png">
</p>


Fully documented
----------------

The [documentation](https://bczsalba.github.io/pytermgui/pytermgui.html) details every public name in the library, making its usage as easy as possible. For more complete projects, check out [examples](/examples), or some of the projects using PTG.


Projects using pytermgui
------------------------

We take pride in seeing others use the library. If you have a project you'd like us to add here, create a PR!

<!-- Add your project below. Try to keep an alphabetical order. -->

| Project name  | Project description | Demo image|
----------------|---------------------|------------
| [`sipedon`](https://github.com/bczsalba/sipedon) | An interactive aquarium for your terminal. | <p align="center"><img src="https://github.com/bczsalba/pytermgui/blob/new-readme/assets/demos/sipedon.png?raw=true" width=50%></p> |
| [`tracers`](https://github.com/bczsalba/sipedon) | Easily debug and trace attribute changes in your Python classes | <p align="center"><img src="https://github.com/bczsalba/pytermgui/blob/new-readme/assets/demos/tracers.png?raw=true" width=50%></p> |


Some showcase images
--------------------

### A hello world program

![hello world](assets/demos/hello_world.png)

-------------------------

### The markup playground app

> Note: Use `ptg --markapp` to try

![markapp](assets/demos/markapp.png)

-------------------------

### A simple window manager demo in 14 lines of code, lifted from the [docs](https://bczsalba.github.io/pytermgui/pytermgui/window_manager.html)

![window manager](assets/docs/wm_demo.gif)

