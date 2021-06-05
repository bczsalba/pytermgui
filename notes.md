IN PROGRESS
-----------

* 0.1.0 release:
    - [ ] `ListView` should have a construction-parameter similar to `Prompt`'s highlight_target
    - [ ] fix whatever is going wrong with `--markup` SyntaxErrors
    - [ ] fix `InputField` up & down

* later releases:
    - `Splitter` rewrite:
        + inherit from `Container`
        + better spacing (obv)
        + fix `selectables_length`

    - `Container.get_lines()` method rethink
        + make it less messy
        + the parent `Container` should send the object an available width & height
        + add size policies
        + while we're at it, the current handling for enums is kinda messy:
            * you set `VERT` & `HORIZ` align as an attribute, but you call a setter with `CENTER`

    - add a syntax style for `InputField`

    - add background styles

    - maybe clean up how Widget "enum" attributes are written

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

* `break_line` should be finished, so that ListView.LAYOUT_HORIZONTAL actually works
