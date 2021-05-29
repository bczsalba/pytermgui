IN PROGRESS
-----------

* fix `InputField` up & down

* add a whole-line style for `InputField`

* `ListView` should have a construction-parameter similar to `Prompt`'s highlight_target

* `break_line` should be finished, so that ListView.LAYOUT_HORIZONTAL actually works

* add background styles

FINISHED
--------

* context managers
    - [x] print_at(tuple[int, int])
    - [x] alt_buffer(cursor: bool)

* ANSI implementation
    - [x] `\033[{0-9}m`
    - [x] 16-color palette
    - [x] 256-color palette
        + [x] 38;5 - fg
        + [x] 48;5 - bg

    - [x] rgb palette
        + [x] 38;5 - fg
        + [x] 48;5 - bg

    - [x] hex palette

* classes
    - [x] Widget

    - [x] Container
        + [x] repr
            * all line based, use `print_at()`
        + [x] add
        + [x] iadd
        + [x] \_add_element

    - [x] Prompt
    - [x] ListView
    - [x] Label

* `_Color` class should do 16, 256, RGB and HEX colors instead of 3 different functions

* `RichLabel` class, or the default fore & background styles being able to read `[cyan]style[/cyan]`

* rewrite the mess that `Container.get_lines` has become. It should be separated into more smaller protected methods.

* templating: dumping and loading from files, strings
