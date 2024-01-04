<!--![title](https://github.com/bczsalba/pytermgui/raw/master/assets/title.png)-->

![title](https://github.com/bczsalba/pytermgui/raw/master/assets/readme/screenshot.png)

> Python TUI framework with mouse support, modular widget system, customizable and rapid terminal markup language and more!

```bash
pip3 install pytermgui
```

<p align=center>
   <a href="https://pypi.org/project/pytermgui">
      <img alt="PyPi project" src="https://img.shields.io/pypi/v/pytermgui?color=brightgreen">
   </a>
    <a href="https://github.com/bczsalba/pytermgui/blob/master/utils/create_badge.py">
      <img alt="Code quality" src="https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/badges/quality.svg">
   </a>
   <a href="http://ptg.bczsalba.com/">
      <img src="https://img.shields.io/badge/documentation-up%20to%20date-brightgreen">
   </a>
   <a href="https://github.com/bczsalba/pytermgui/actions/workflows/pytest.yml">
      <img src="https://github.com/bczsalba/pytermgui/actions/workflows/pytest.yml/badge.svg">
   </a>
 </p>
 <p align=center>
   <a href="https://discord.gg/g4bqMvpG4U">
      <img src="https://img.shields.io/discord/999374285686706367?label=join%20our%20discord">
   </a>
</p>

## Notice

A much better, more complete version of PTG's core ideas now exists over at [Shade 40](https://github.com/shade40). While PTG is not yet fully obsolete,
those libraries will be the primary focus of development going forward.

<hr>

## Why?

Mostly because terminals are cool, but creating terminal apps has historically been difficult. PyTermGUI aims to provide a simple, readable and modular way to make the app of your dreams!

Terminal apps are (often):

- Easier to install
- Faster & more resource efficient
- Less prone to differences between environments (no IE7 here!)

...than their web or native counterparts.

## How?

We provide a couple of things to make your life easier:

- Sensible abstractions over most terminal standards
- A fully fledged, desktop-inspired window manager system with modals and completely customizable windows
- Mouse support out of the box with **0** configuration
- YAML (or Python) based styling engines
- TIM, our markup language for creating styled terminal text with expressive text, including systems for aliases & macros
- A bunch of things I can't think of right now :slightly_smiling_face:

Additionally, there are a couple of neat tools to make your general Python development easier:

- An inspection utility
- A pretty printer for both the REPL and IPython
- A way to create SVG and HTML screenshots of your terminal

<!-- HATCH README END -->

## Examples

> All images below are generated directly from the source displayed by a PyTermGUI-powered SVG exporter tool, [Termage](https://github.com/bczsalba/termage).

Your first application, a simple clock:

```python3
import time

import pytermgui as ptg

def macro_time(fmt: str) -> str:
    return time.strftime(fmt)

ptg.tim.define("!time", macro_time)

with ptg.WindowManager() as manager:
    manager.layout.add_slot("Body")
    manager.add(
        ptg.Window("[bold]The current time is:[/]\n\n[!time 75]%c", box="EMPTY")
    )
```

Since strings are converted into the `Label` widget, and all widgets use markup for styling, we can use a custom-defined TIM macro function to return the current time. After running the above, you should see something like:

<p align="center">
    <img alt="Clock example output" src="https://github.com/bczsalba/pytermgui/raw/master/assets/readme/clock.svg">
</p>

For something a bit more in-depth, see this contact form inspired by [asciimatics' example](https://github.com/peterbrittain/asciimatics#how-to-use-it):

```python3
import pytermgui as ptg

CONFIG = """
config:
    InputField:
        styles:
            prompt: dim italic
            cursor: '@72'
    Label:
        styles:
            value: dim bold

    Window:
        styles:
            border: '60'
            corner: '60'

    Container:
        styles:
            border: '96'
            corner: '96'
"""

with ptg.YamlLoader() as loader:
    loader.load(CONFIG)

with ptg.WindowManager() as manager:
    window = (
        ptg.Window(
            "",
            ptg.InputField("Balazs", prompt="Name: "),
            ptg.InputField("Some street", prompt="Address: "),
            ptg.InputField("+11 0 123 456", prompt="Phone number: "),
            "",
            ptg.Container(
                "Additional notes:",
                ptg.InputField(
                    "A whole bunch of\nMeaningful notes\nand stuff", multiline=True
                ),
                box="EMPTY_VERTICAL",
            ),
            "",
            ["Submit", lambda *_: submit(manager, window)],
            width=60,
            box="DOUBLE",
        )
        .set_title("[210 bold]New contact")
        .center()
    )

    manager.add(window)
```

This showcases the YAML-based config system, as well as some additional API. I recommended checking out the [source file](https://github.com/bczsalba/pytermgui/blob/master/utils/readme_scripts/contact.py) to see how the `submit` callback works.

<p align="center">
    <img alt="Contact form example output" src="https://github.com/bczsalba/pytermgui/raw/master/assets/readme/contact.svg">
</p>

## Not a fan of colors? We've got you!

PyTermGUI is one of the only TUI libraries that offers [NO_COLOR](https://no-color.org) support that doesn't ~~suck~~ ruin the usability & design of your apps.

This is how the above example looks like with the environment variable `NO_COLOR` set to anything. Note how contrast between colors is retained, as well as the inclusion of background colors:


<p align="center">
    <img alt="Contact form NO_COLOR output" src="https://github.com/bczsalba/pytermgui/raw/master/assets/readme/contact_no_color.svg">
</p>


## Older terminals? No problem!

We use algorithms based on human vision to convert and downgrade colors when the current terminal emulator doesn't support them. Here is a cool screenshot:

<p align="center">
    <img alt="Contact form NO_COLOR output" src="https://github.com/bczsalba/pytermgui/raw/master/assets/readme/colorgrids.png">
    <figcaption><em>Disclaimer:</em> Termage currently doesn't play nicely to changing colorsystems during runtime, so this image had to be captured natively :(</figcaption>
</p>


## Questions? See the docs!

Pretty much every single name in the library, private or public, has an insightful dockstring attached to it, and we are accumulating a growing amount of walkthrough-based documentations articles. See 'em all on the [doc website](https://ptg.bczsalba.com)!


## Contributions, issues et al.

If you have any problems using the library, feel free to open up a discussion or raise an issue ticket. If you would prefer to hack on the library yourself, see the [contribution guidelines](https://github.com/bczsalba/pytermgui/blob/master/CONTRIBUTING.md). Pull requests are encouraged, but make sure you aren't trying to fix an issue that others are already working on, for your own sake. :slightly_smiling_face:
