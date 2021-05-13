IN PROGRESS
-----------

* ANSI implementation
    - [ ] look into if key codes (like UP) work universally or need to be platform-specific

* `ListView` should have a construction-parameter similar to `Prompt`'s highlight_target
* look into why `ProgressBar` ends one short when it doesn't have a `forced_width`
* add background styles
* `break_line` should be finished, so that ListView.LAYOUT_HORIZONTAL actually works
* templating: dumping and loading from files, strings

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
