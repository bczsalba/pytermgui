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
   <a href="https://github.com/bczsalba/pytermgui/actions/workflows/pytest.yml">
      <img src="https://github.com/bczsalba/pytermgui/actions/workflows/pytest.yml/badge.svg">
   </a>
 </p>
 <p align=center>
   <a href="https://twitter.com/bczsalba">
   <img alt="Twitter" 
        src="https://img.shields.io/twitter/url/https/twitter.com/bczsalba.svg?style=social&label=Follow%20%40bczsalba">
   </a>
   <a href="https://ko-fi.com/bczsalba" title="Donate to this project using Ko-Fi">
      <img src="https://img.shields.io/badge/ko--fi%20-donate-%232aabe0" alt="Buy Me A Coffee donate button" />
   </a>
</p>


## Usecases

PyTermGUI can be used for a variety of things. You are ought to find something useful, whether you are after a TUI library with a [mature widget API](), a way to easily color and style your program's output or even just get syntax highlighting in the REPL.


### Interfacing with the terminal

At its core, PyTermGUI is based on the [ANSI interface](https://ptg.bczsalba.com/pytermgui/ansi_interface.html) module to provide pretty much all of the raw terminal capabilities. If you just want easy, Pythonic access to these APIs `ansi_interface` was made just for you!

```python3
from pytermgui import print_to, report_cursor, bold

print_to((10, 5), "12345"); report_cursor()
```

<p align=center>
   <img alt="ANSI example" src="https://github.com/bczsalba/pytermgui/raw/master/assets/readme/ansi.png">
</p>


### Using TIM to style your program's output

TIM, our **T**erminal **I**nline **M**arkup language provides an easy to read, semantic and performant way to style your text. It is also modular and extensible, supports macros, in-terminal hyperlinks, all commonly used ANSI styles & colors, RGB & HEX and more!

```python3
from pytermgui import tim

tim.print("[dim italic]Welcome to [/dim /italic bold !rainbow]PyTermGUI")
tim.print("Check out the [blue !link(https://ptg.bczsalba.com)]docs[/!link /fg]!")
```

![TIM example](https://github.com/bczsalba/pytermgui/raw/master/assets/readme/tim.png)

In this demo, clicking `docs` will bring you to the [documentation](https://ptg.bczsalba.com).


### Prettification

You can prettify all REPL output using just **one line** of code! It supports various datatypes, automatic printing of PyTermGUI and Rich objects and more!

Under the hood it calls `tim.setup_displayhook()` with no arguments. For more granular control, including flattening structures and customizing the colors, check out the [TIM docs](https://ptg.bczsalba.com/pytermgui/parser.html)!

```python3
>>> from pytermgui import pretty
>>> ["Welcome to PyTermGUI!", {0: "Things are now", 1: "Prettier!"}, locals()]
>>> '[dim]TIM [/dim]code is automatically [!gradient(222)]syntax-highlighted'
```

![Pretty example](https://github.com/bczsalba/pytermgui/raw/master/assets/readme/pretty.png)


### Code-introspection

PyTermGUI offers an `Inspector` widget, as well as a higher level wrapper function, `inspect` that can be used to see detailed & pretty information on any Python object, including its documentation, methods, clickable hyperlink to its source & more!

It can be used programatically using the `ptg.inspect` name, or from the cli by running `ptg -i <import_path>`. You can also use the `-e` flag to inspect the result of an expression after executing it.

**Pro Tip**: All `PyTermGUI` objects are included in the CLI inspection namespace, so you can use `Container` instead of `pytermgui.Container`.


![inspect example](https://github.com/bczsalba/pytermgui/raw/master/assets/readme/inspect.png)

See the [docs](https://ptg.bczsalba.com/pytermgui/inspector.html) or `ptg -i inspect` for more info!


### Creating useful and beautiful TUIs, quickly

You can check out an example TUI built into the library itself using the `ptg` command! It features some utility applications for PyTermGUI, such as an `xterm-256` & rgb colorpicker, a TIM sandbox, an inspector and a simple key-getter.

You can also follow a how-to guide on creating a simple application in the [docs](https://ptg.bczsalba.com/pytermgui.html), or look at some [examples](https://github.com/bczsalba/pytermgui/tree/master/examples).

![TUI example](https://github.com/bczsalba/pytermgui/raw/master/assets/readme/tui.png)


### Compatibility

Using some color math, PyTermGUI provides graceful color degradation from RGB all the way to the standard, `xterm-16` colors. This allows you to write your program with the exact colors you want, and let the library worry about the end-user's terminal capabilities.

<p align="center">
<img alt="Graceful degradation" src="https://github.com/bczsalba/pytermgui/raw/master/assets/readme/degradation.png">
</p>


### NO_COLOR=1 support that doesn't suck

Most libraries completely omit colors when [NO_COLOR](https://no-color.org) is set. This _works_ but completely kills legibility since it doesn't keep any contrast. PyTermGUI uses a human-vision based lightness model to convert any color into a greyscale variant, so your interface will remain usable even with no colors available.

It also happens to be a great way to test contrast between colors while making a new TUI. If differences between elements aren't obvious in `NO_COLOR=1`, they won't be obvious in normal colors.

![NO_COLOR example](https://github.com/bczsalba/pytermgui/raw/master/assets/readme/no_color.png)


## No constraints

This library was built with the goal of allowing the most amount of customizability at each step of the process. This is due to my own personal experience with other similar projects, where I felt too confined into a certain program-architecture, way to express colors and the like. PyTermGUI aims to shed all of those limits to truly put you in control.

For example, you can define a `Window` in a couple of ways:

**Instantiating it with its children as the arguments**

```python3
# -- demo.py --
import pytermgui as ptg

with ptg.WindowManager() as manager:
   demo = ptg.Window(
      ptg.Label("[210 bold]Hello world!"),
      ptg.Label(),
      ptg.InputField(prompt="Who are you?"),
      ptg.Label(),
      ptg.Button("Submit!")
   )
   
   manager.add(demo)
   manager.run()
```

**Converting builtin datatypes into widgets**

```python3
# -- demo.py --
import pytermgui as ptg

with ptg.WindowManager() as manager:
   demo = (
       ptg.Window()
       + "[210 bold]Hello world!"
       + ""
       + ptg.InputField(prompt="Who are you?")
       + ""
       + ["Submit!"]
   )
   
   manager.add(demo)
   manager.run()
```

**Definining the whole thing in YAML**

*Note that for YAML functionality the optional `PyYAML` dependency is required.*

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

# Run `ptg -f demo.yaml` to interpret this file
```

These all give you the exact same result, while allowing you to pick the best syntax for each case. I personally find YAML to be a great way to prototype complex widget layouts without having to write any driving code.

For completeness' sake, here is the `Window` we just created:

![Example window](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/demos/versatility.png)


## The `ptg` command line utility

As mentioned above, the `ptg` CLI tool is a great example for both the capabilities of the library and how to make use of it. It also provides some simpler helpers, such as `--size` to retrieve your terminal dimensions, and the `--file` argument which allows you to load and play around with a PTG YAML file.

See `ptg -h` for more info.


## Documentation!

*Every single* public and non-public name in the library is fully documented, using [Google's docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings). If you ever have questions about the library, the documentation should have your answers.

## Contributions welcome!

PyTermGUI will only become its best self if its users have their say. As such, we provide a [contribution](https://github.com/bczsalba/pytermgui/blob/master/CONTRIBUTING.md) guide and are open to issues, suggestions and PRs!

All input is appreciated.

## Some projects using PyTermGUI

We take pride in seeing others use the library. If you have a project you'd like us to add here, create a PR!

<!-- Add your project below. Try to keep an alphabetical order. -->

| Project name                                     | Project description                                             | Demo image                                                                                                                      |
| ------------------------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| [`sipedon`](https://github.com/bczsalba/sipedon) | An interactive aquarium for your terminal.                      | <p align="center"><img src="https://github.com/bczsalba/pytermgui/blob/master/assets/demos/sipedon.png?raw=true" width=80%></p> |
| [`tracers`](https://github.com/bczsalba/tracers) | Easily debug and trace attribute changes in your Python classes | <p align="center"><img src="https://github.com/bczsalba/pytermgui/blob/master/assets/demos/tracers.png?raw=true" width=80%></p> |


## Examples

The `examples/` directory contains some nice showcases of the library. Here are some of them:

*Click on each image to see their source code*

### A hello world program

[![hello world](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/demos/hello_world.png)](examples/hello_world.yaml)

### The TIM playground app

> Note: Use `ptg -t` to try

[![TIM](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/demos/timwin.png)](pytermgui/cmd.py)

### A simple window manager demo in 13 lines of code, lifted from the docs

[![window manager](https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/wm_demo.gif)](https://bczsalba.github.io/pytermgui/pytermgui/window_manager.html)


## Projects to check out

The TUI game has been heating up as of recent. Here are some other interesting projects in the sphere:
- [Winman](https://github.com/epiclabs-io/winman) - A window-manager add-on to the golang library [tview](https://github.com/rivo/tview). This project was a big inspiration for that specific aspect of PyTermGUI.
- [Rich & Textual](https://github.com/textualize) - Another Python-based set of TUI libraries. Some of the Rich markup syntax & code was used as inspiration for our own.
- [pyTermTk](https://github.com/ceccopierangiolieugenio/pyTermTk) - Name and functionality sibling of this project. Great TUI library if you are after tkinter/qt5 mimicking API.
- [Jexer](https://jexer.sourceforge.io/) - One of the most insane-looking TUI libraries out there. Supports practically everything the terminal can do. I became aware of this project relatively recently, but it's been of great inspiration.
- [notcurses](https://github.com/dankamongmen/notcurses) - Another ridiculously powerful TUI library. Well worth installing and checking out the examples provided.


## Consider donating

PyTermGUI takes up pretty much all of my freetime outside of work and university. Donations are always invested back into the project in some way, be it for better equipment or just extra motivation to continue working on it.

Do note that functionality will **never** be limited behind a paywall. All donations are completely optional, only serving as a way to say "thanks".

You can check out my [Ko-fi page](https://ko-fi.com/bczsalba) for more information.
