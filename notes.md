IN PROGRESS
-----------

* `Splitter`
    - that exception really doesn't need to be there, the program should be able to handle the situation
    - `ListView` doesn't align properly to the right when in a `Splitter`

* add a `focus()` method to `Widget`, that sets some private attribute (like `is_selected` = True)
* fix `InputField` up & down

* `ListView` should have a construction-parameter similar to `Prompt`'s highlight_target

* look into why `ProgressBar` ends one short when it doesn't have a `forced_width`

* add background styles

* `break_line` should be finished, so that ListView.LAYOUT_HORIZONTAL actually works

* templating: dumping and loading from files, strings

* rewrite the mess that `Container.get_lines` has become. It should be separated into more smaller protected methods.

* `RichLabel` class, or the default fore & background styles being able to read `[cyan]style[/cyan]`


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
