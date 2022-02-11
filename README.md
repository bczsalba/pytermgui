<!-- TODO: these colors could be randomly generated -->

![title](https://github.com/bczsalba/pytermgui/raw/master/assets/title.png)

> A simple yet powerful TUI framework for your Python (3.7+) applications

```
pip3 install pytermgui
```

<p align=center>
   <a href="https://pypi.org/project/pytermgui">
      <img alt="PyPi project" src="https://img.shields.io/pypi/v/pytermgui?color=brightgreen">
   </a>
    <a href="https://github.com/bczsalba/pytermgui/blob/master/utils/create_badge.py">
      <img alt="Code quality" src="https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/badges/quality.svg">
   </a>
   <a href="https://reddit.com/r/pytermgui">
      <img src="https://img.shields.io/reddit/subreddit-subscribers/pytermgui?style=flat&color=bright-green">
   </a>
   <a href="http://ptg.bczsalba.com/pytermgui.html">
      <img src="https://img.shields.io/badge/documentation-up%20to%20date-brightgreen">
   </a>
 </p>

## Batteries included or bare-metal. It's your choice.

PyTermGUI has both higher and lower level interfaces. If you're only here for the terminal APIs, `ansi_interface` will be your friend.

## Zero dependencies

Everything here is home made, just like your grandmas cookies. There is only one optional dependency, `PyYaml`, which you won't have to install unless you plan on using YAML features.

## Adapting to your needs

Here are just a couple of ways to define the same widget structure:

**Using the basic class structure**

```python3
# -- demo.py --
import pytermgui as ptg

demo = ptg.Window(
   ptg.Label("[210 bold]Hello world!"),
   ptg.Label(),
   ptg.InputField(prompt="Who are you?"),
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
what _we_ want, rather encourage you to morph the library around your needs.

By the way, this is what the created `Window` looks like. Nifty, huh?

<p align="center">
    <img src="https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/demos/versatility.png">
</p>

## A powerful CLI

The [cli](/pytermgui/cmd.py) simultaneously serves as a set of powerful tooling for TUI related work, as well as a nice usage example of the higher level part of the library. You can run `ptg --getch` to get information about a keypress, `ptg --size` to get the current terminal dimensions and `ptg --file <file>` to interpret & run a YAML markup file inside of a window manager.

For more info, check out `ptg -h`.

## Fully documented

The [documentation](http://ptg.bczsalba.com/pytermgui.html) details every public name in the library, making its usage as easy as possible. For more complete projects, check out [examples](/examples), or some of the projects using PTG.

## Projects using pytermgui

We take pride in seeing others use the library. If you have a project you'd like us to add here, create a PR!

<!-- Add your project below. Try to keep an alphabetical order. -->

| Project name                                     | Project description                                             | Demo image                                                                                                                      |
| ------------------------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| [`sipedon`](https://github.com/bczsalba/sipedon) | An interactive aquarium for your terminal.                      | <p align="center"><img src="https://github.com/bczsalba/pytermgui/blob/master/assets/demos/sipedon.png?raw=true" width=80%></p> |
| [`tracers`](https://github.com/bczsalba/tracers) | Easily debug and trace attribute changes in your Python classes | <p align="center"><img src="https://github.com/bczsalba/pytermgui/blob/master/assets/demos/tracers.png?raw=true" width=80%></p> |

## Some showcase images

Click on each image to see their source code!

### A hello world program

[![hello world](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/demos/hello_world.png)](examples/hello_world.yaml)

### The markup playground app

> Note: Use `ptg --markapp` to try

[![markapp](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/demos/markapp.png)](pytermgui/cmd.py)

### A simple window manager demo in 13 lines of code, lifted from the docs

[![window manager](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/wm_demo.gif)](https://bczsalba.github.io/pytermgui/pytermgui/window_manager.html)
