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
        ["Exit", lambda *_: manager.exit()],
    )
    
    manager.add(window)
    manager.run()
```

## Adding windows during definition

You don't need to assign your window to a variable if you aren't going to reference it later. Since all widgets implement `__add__` and `__iadd__`, you can define them as a sum of other widgets.

For example:

```python3
import pytermgui as ptg

with ptg.WindowManager() as manager:
    manager.add(
        ptg.Window()
        + "[wm-title]My first window!"
        + ""
        + ["Exit", lambda *_: manager.exit()]
    )
    
    manager.run()
```

## Useful methods to know about

- `pytermgui.widgets.Widget.bind`: Bind a keypress to an action. You can also add a description, which you can then use to have a sort of help menu.
- `pytermgui.parser.MarkupLanguage.alias`: Alias a single word (with no spaces) to some markup.
- `pytermgui.parser.MarkupLanguage.define`: Define a markup macro. See `pytermgui.parser` for info on the macro functionality.

**Note:** For markup functions, it is recommended to use the `markup` name that is exported by the module.

```python3
import pytermgui as ptg

ptg.markup.alias("my-tag", "blue @141")

with ptg.markup as mprint:
    mprint("This is [my-tag]my-tag!")
```

# How to: Configure your Application using `YAML`

## Why you should bother

While the programmatic interface for the style system is *alright*, it's a bit clunky to use for serious customization. In order to improve your experience, you can use a YAML file with your configuration in its `config` section. Additionally, you can define markup in a nicer way as well.

For the purposes of this guide, we will use YAML defined inside our Python code. `pytermgui.file_loaders.FileLoader.load` can take etiher strings or files, so the `PTG_CONFIG` name below can be trivially modified to refernce a file.

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
        + ["Exit", lambda *_: manager.exit()]
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

**Note:** While it is permitted, not including `depth` nor `item` into your markup will turn it static, likely causing some headaches.

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

**Note:** We used the `&` and `*` symbols above. In YAML, `&` creates a named anchor point, and `*` allows you to reference it. [Here](https://medium.com/@kinghuang/docker-compose-anchors-aliases-extensions-a1e4105d70bd) is a cool article on the subject.

<p align="center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/yaml/config_basic.png
    style="width: 80%">
</p>


# How to: Define widgets in YAML

## Setup

The file loader system also has support for defining entire widgets in files, as can be seen by the [hello world example](https://github.com/bczsalba/pytermgui/blob/master/examples/hello_world.yaml).

These files can be interpreted with a CLI flag and require no actual code to "run".

This is how the `widgets` section of the file should look like:

```yaml
widgets:
    WidgetName:
        type: WidgetTypeKnownToPTG
        arbitrary-attribute: arbitrary-value

    # Alternatively, if you don't need your widget to be named,
    # this syntax will automatically assign `type` to the key provided.
    WidgetTypeKnownToPTG:
        arbitrary-attribute: arbitrary-value
```

Where `WidgetTypeKnownToPTG` *must* be a widget subclass either included in the library by default, or registered using the loader's serializer. The second is only possible when you are interpreting it from Python yourself, and not when you use `ptg -f`.

Registering a widget goes as follows:

```python3
import ptg as pytermgui

class YourCustomWidget(ptg.Widget):
    ...
    
serializer = ptg.Serializer()
serializer.register(YourCustomWidget)

loader = ptg.YamlLoader(serializer)

with open("your-file.yaml", "r") as ptg_file:
    namespace = loader.load(serializer)
```

All of the `FileLoader` subclasses take a `pytermgui.serializer.Serializer` instance as their first argument, setting up their own if one was not given. This object is then used to instantiate all of the widgets it encounters, so registering a widget to it will allow the loader to use it.

**Note:** Serializers can dump any, even unknown widget types, but **can only load known ones**.

Once all your widgets are registered and load correctly, you can access them by the `WidgetName` attribute of your namespace.

## Loading a namespace using `ptg -f`

The simplest way to use these files is running `ptg -f "filename"`, where `filename` points to your namespace file. As mentioned above, **you can only use PTG native widget types** with this method.

What that CLI tool does is essentially this:

```python3
import pytermgui as ptg

with open(args.file, "r") as file:
    namespace = ptg.YamlLoader().load(args.file)

with ptg.WindowManager() as manager:
    for widget in namespace.widgets:
        manager.add(widget)

    manager.run()
```

## Loading a namespace programatically

Loading namespaces manually is more or less defined above, with one extra detail. You can either loop through all defined widgets as show previously, or reference them as the key they were defined as in your namespace file.

For example:

```yaml
widgets:
    MyWidget:
        ...
```

...where `...` would be filled with your data, would allow you to use

```python3
my_widget = namespace.MyWidget
```

...to reference the instance that was created.

**Note:** This is the specific instance the loader created. If you plan on using this as a sort of template, be sure to run `copy()` before modifying your widget.

## Defining widget attributes

So, now that you know how to get your namespace file loaded, let's get some information into it.

The syntax goes like this:

```yaml
widgets:
    WidgetName:
        type: WidgetType
        widgets:
            - WidgetType:
                arbitrary-attribute: arbitrary-value

        arbitrary-attribute: arbitrary-value
```

As you can see, any arbitrary attribute can be set in this method. You can also define a **list** of widgets, using the `widgets` key. The loader only looks for keys **starting with** `widgets`, so you can separate your widgets into categories or groups if that tickles your fancy.

For example:

```yaml
widgets:
    MyContainer:
        type: Container
        widgets_header:
            - Label:
                value: This is my header
            - Label:
                value: ""

        widgets_body:
            - Button:
                label: Press me
```

This syntax is the equivalent of putting all three widget definitions under one `widgets` key.

## Defining custom boxes

The `boxes` section allows you to define your own **namespace file local** `pytermgui.widgets.boxes.Box` classes. **You may only use these within the file they were defined in**.

**Note:** The preferred naming convention for boxes is `WHATEVER_THIS_IS`. Not sure why, but that's how all the native boxes were defined and it stands out enough for clarity.

A basic box definition would go like this:

```yaml
boxes:
    MY_BOX: [
        "0bbb1",
        "a x c",
        "3ddd2"
    ]
```

In this example, we would get a box with the corner characters 

```yaml
["0", "1", "2", "3"]
```

...and border characters

```yaml
["a", "b", "c", "d"]
```

For more information on the semantics of boxes, check out `pytermgui.widgets.boxes.Box`. The characters defined here are directly passed to the `Box` constructor.

## Combining our knowledge to create an application

Using everything we learnt above, we can define a simple application:

### namespace.yaml

```yaml
config:
    Window:
        styles:
            border: &w-border-style "[#5A6572]{item}"
            corner: *w-border-style

    Container:
        styles:
            border: &c-border-style "[#7D98A1]{item}"
            corner: *c-border-style

    Button:
        styles:
            label: "[@#1C2220 #A9B4C2]{item}"
            highlight: "[#1C2220 @#A9B4C2]{item}"

    Splitter:
        chars:
            separator: "   "

boxes:
    OUTER: [
        "█▀▀▀█",
        "█ x █",
        "█▄▄▄█",
    ]

markup:
    title: "#A9B4C2 bold"
    subtitle: "italic dim"
    body: "245"

widgets:
    MainWindow:
      type: Window
      box: OUTER
      width: 70
      widgets:
        - Label:
            value: "[title]YAML is cool!"
        - Label: {}

        - Label:
            value: "[subtitle]Here are some facts about it:"
        - Label: {}

        - Splitter:
            widgets:
                - Container:
                    box: OUTER
                    widgets:
                        - Label:
                              value: >-
                                -[body] YAML originally stood for "Yet Another Markup
                                Language", but was later modified to mean "YAML Ain't 
                                Markup".

                              parent_align: 0

                - Container:
                    box: OUTER
                    widgets:
                        - Label:
                              value: >-
                                -[body] The language was designed by Clark Evans, Ingy
                                döt Net and Oren Ben-Kiki.

                              parent_align: 0

        - Label: {}
        - Button:
            id: button-definition
            label: Get definition

    PopupWindow:
        type: Window
        is_modal: true
        width: 50

        box: OUTER
        widgets:
            - Label:
                value: "[title]YAML is defined as..."
            - Label: {}

            - Label:
                value: "[body]...a human-readable data-serialization language."
            - Label: {}

            - Label:
                parent_align: 0
                value: "[body italic]Press CTRL_W to close this window."
```

### runner.py

```python3
import pytermgui as ptg

namespace = ptg.YamlLoader().load(PTG_NAMESPACE)

with ptg.WindowManager() as manager:
    manager.add(namespace.MainWindow.center())

    popup = namespace.PopupWindow.center()
    popup.bind(ptg.keys.CTRL_W, lambda window, _: window.close())

    button = ptg.get_widget("button-definition")
    button.onclick = lambda *_: manager.add(popup)

    manager.run()
```

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/yaml/config_advanced0.png
    style="width: 80%">
</p>

<p style="text-align: center">
    <img src=https://raw.githubusercontent.com/bczsalba/pytermgui/master/assets/docs/init/yaml/config_advanced1.png
    style="width: 80%">
</p>

# How to: Define your own Widget

As mentioned above, you **usually** don't have to do this. `pytermgui` tries to make everything definable inline, but for some functionalities you might need more than what is exposed.

## Important things to know

Firstly, the most important aspect of how the library works is the `pytermgui.window_manager` threading system. As listening for any IO, let it be keyboard or mouse, is always blocking, we cannot print while that is happening. This obviously will not do, so we separate the input and output to different threads.

The main thread is input. This thread is completely handled by the library, and the only place the user can influence it is with the `pytermgui.widgets.base.Widget.bind` system.

The secondary thread handles the output. This is where the users (you) are able to have a say, as most widget code is run here.

## Everything a ~~girl~~ widget needs

You should **always** subclass `pytermgui.widgets.base.Widget` when creating your own widget. There is a lot of abstractions, implementations and all sort of useful junk that the base class does, and reimplementing it is almost never a good idea. (Though if you manage to reimplement a feature-complete Widget class in a better manner than the library does, PRs are always welcome!)

## The things you should define

For any output, use the `get_lines` method. This returns a `list[str]`, where each item of the list is **exactly as long as the widget is wide**, and the length of the list is equal to the height of your widget. What goes in this list is completely up to you, pytermgui will render it as long as it fits those criteria. If you need to do any blocking or long actions for your UI's contents, it is best to do that in a thread and have the thread update some instance attribute, which can then be displayed here. This method is called *a lot* (at least once a frame, usually more), so keep it performant.

For mouse interaction, use `handle_mouse`. This gets a `MouseEvent` and `MouseTarget` as its arguments, and should return **True if widget.select should be run by the caller, False otherwise**. The return value generally stands for whether the given widget could handle the input, but sometimes the above distinction is useful to know about.

For handling keyboard input, use `handle_key`. This simply gets a `str` key as its argument, and should return **True if input was handled, False otherwise**. It should also call `self.execute_binding(key)` before it does any of its own handling, as bindings enjoy priority over normal keyboard actions.

For having a number of suboptions within the widget, define the `selectables_length` property. This is defined by `Container` already, so if you subclass any of its children you won't have to worry about it. `selectables_length` defines how many options can be selected within the widget, and is checked by its parent. Be sure to make it a `@property`, otherwise you will get errors.

For custom styles & chars, define those attributes in the widget body. There is plenty of examples in the `pytermgui.widgets` submodule on how to do this.

# Layers of the API

The API has a strict layered structure. Modules can only use names defined below them in the structure, as such a `Widget` has no clue about a `WindowManager`, unless it has a strictly defined reference to it.

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
