# Getting started

Getting started with pytermgui is quite easy. The library allows you to define layouts inline, thus letting you get by without ever having to subclass Widget or WindowManager. However, if you do want that functionality the later sections of this guide will tell you how to.

# How to: Create your own app

## Most primitive usecase

To create your own app, it is recommended to use the `pytermgui.window_manager.WindowManager` context. Technically, all that is needed for the app to run correctly is to call `pytermgui.window_manager.WindowManager.run` with no arguments.

```python3
import pytermgui as ptg

with ptg.WindowManager() as manager:
    manager.run()
```

This will give you an empty screen you can quit using `CTRL_C`. That is doesn't really get us anywhere though, does it?


## Adding windows as variables
In order to actually have something going on, you can call `pytermgui.widgets.WindowManager.add` with a window of your choice. Adding a window to the manager will bring it to focus.

Here is a quick example of the most basic usecase:

```python3
import pytermgui as ptg

with ptg.WindowManager() as manager:
    window = ptg.Window(
        "[wm-title]My first window!",
        "",
        ["Exit", lambda *_: sys.exit()],
    )
    
    manager.add(window)
    manager.run()
```

## Adding windows during definition

You don't need to assign your window to a variable if you aren't going to reference it later. Since all widgets implement `__add__` and `__iadd__`, you define them as a sum of other widgets.

For example:

```python3
import pytermgui as ptg

with ptg.WindowManager() as manager:
    manager.add(
        ptg.Window()
        + "[wm-title]My first window!",
        + "",
        + ["Exit", lambda *_: sys.exit()],
    )
    
    manager.run()
```

## Useful methods to know about

- `pytermgui.widgets.Widget.bind`: Bind a keypress to an action. You can also add a description, which you can then use to have a sort of help menu.
- `pytermgui.parser.MarkupLanguage.alias`: Alias a single word (with no spaces) to some markup.
- `pytermgui.parser.MarkupLanguage.define`: Define a markup macro. See `pytermgui.parser` for info on the macro functionality.

Note: For markup functions, it is recommended to use the `markup` name that is exported by the module.

```python3
import pytermgui as ptg

ptg.markup.alias("my-tag", "blue @141")

with ptg.markup as mprint:
    mprint("This is [my-tag]my-tag!")
```

# How to: Configure your Application using inline YAML

## Why you should bother

While the programmatic interface for the style system is *alright*, it's a bit clunky to use for serious customization. In order to improve your experience, you can use a YAML file with your configuration in its `config` section. Additionally, you can define markup in a nicer way as well.

**Note:** You will need to install `PyYAML` in order to use the YAML loader class.

## Base application

For the purposes of this section, this is the application we will use:

```python3
import sys
import pytermgui as ptg

# Define empty config as the base
# 
# Note that we define markup tags as empty.
# markup tags **need** to be defined for program
# execution.
PTG_CONFIG = """\
config: {}

markup:
    title: ""
    body: ""
"""

with ptg.WindowManager() as manager:
    # Initialize a loader, and load our config
    loader = ptg.YamlLoader()
    loader.load(PTG_CONFIG)

    # Create a test window
    manager.add(
        ptg.Window()
        + "[title]This is our title"
        + ""
        + {"[body]First key": ["First button"]}
        + {"[body]Second key": ["Second button"]}
        + {"[body]Third key": ["Third button"]}
        + ""
        + ["Exit", lambda *_: sys.exit()]
    )

    manager.run()
```

This gives us the following, very bland interface.

<p align="center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/yaml/base.png
    style="width: 80%">
</p>

## Adding markup

As you could see above, defining markup aliases is quite easy. You cannot and will possibly never be able to define macros in a markup file for two main reasons:
- It would be a nightmare to implement in terms of technicalities
- It would be a hotbed for RCE security risks

There is some leeway on both of those however, and that may be revisited in the future.

Anyways, markup aliases. The `markup` section of your file should be the following format:

```yaml
markup:
    alias-name: alias-value
```

...which would stand for

```python3
ptg.markup.alias("alias-name", "alias-value")
```

You should not include `[` and `]` delimiters around either arguments.

As an example, let's expand our `PTG_CONFIG` from above:

```yaml
config: {}

markup:
    title: 210 bold
    body: 245 italic
```

<p align="center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/yaml/markup.png
    style="width: 80%">
</p>

Getting there.

## Customizing widget styles & chars

The markup configuration allows for quite a bit more customization, using the thus-far untouched config section.

The basic syntax goes as follows:

```yaml
config:
    WidgetName:
        styles:
            style_key: markup_str

        chars:
            char_key: char_str
```

As you can see, styles take markup strings. This is because they are converted right into `pytermgui.styles.MarkupFormatter` objects, which means you can incorporate both `{depth}` and `{item}` into them.

**Note**: While it is permitted, not including `depth` nor `item` into your markup will turn it static, likely causing some headaches.

So for a simple example, let's define some styles & chars:

```yaml
config:
    Window:
        styles:
            border: &border-style "[60]{item}"
            corner: *border-style

    Button:
        styles:
            label: "[@235 108 bold]{item}"
    
    Splitter:
        chars:
            separator: "   "

markup:
    title: 210 bold
    body: 245 italic
```

**Note**: We used the `&` and `*` symbols above. In YAML, `&` creates a named anchor point, and `*` allows you to reference it. [Here](https://medium.com/@kinghuang/docker-compose-anchors-aliases-extensions-a1e4105d70bd) is a cool article on the subject.

<p align="center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/yaml/config_basic.png
    style="width: 80%">
</p>


# Layers of the API

## Low level

At the base, there is `pytermgui.ansi_interface` and `pytermgui.input`, handling terminal APIs for output and input respectively. This is the lowest-level layer of the library.

```python3
import pytermgui as ptg

ptg.set_alt_buffer()

print('This terminal will be discarded on r"\n" input.')
while ptg.getch() != r"\n":
    print("Wrong key.")

ptg.unset_alt_buffer()
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/low.png
    style="width: 80%">
</p>


## Helper level

On top of that, there is the helper layer, including things like `pytermgui.helpers`, `pytermgui.context_managers` and the kind. These provide no extra functionality, only combine functions defined below them in order to make them more usable.

```python3
import pytermgui as ptg

text = r"This is some \033[1mlong\033[0m and \033[38;5;141mstyled\033[0m text."

for line in ptg.break_line(text, limit=10):
    print(line)
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/helper.png
    style="width: 80%">
</p>


## High level

Building on all that is the relatively high level `pytermgui.widgets` module. This part uses things from everything defined before it to create a visually appealing interface system. It introduces a lot of its own APIs and abstractions, and leaves all the parts below it free of cross-layer dependencies.

The highest layer of the library is for `pytermgui.window_manager`. This layer combines parts from everything below. It introduces abstractions on top of the `pytermgui.widget` system, and creates its own featureset. 

```python3
import pytermgui as ptg
with ptg.WindowManager() as manager:
    manager.add(
        ptg.Window()
        + "[141 bold]Title"
        + "[grey italic]body text"
        + ""
        + ["Button"]
    )
    manager.run()
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/high.png
    style="width: 80%">
</p>
