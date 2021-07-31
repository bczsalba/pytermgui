IN PROGRESS
-----------

* version 0.1.4:
    - Improvements to the `Button` class
    - Improvements to targeting
    - Fix performance

* version 0.1.5:
    - `Splitter()` rewrite
    - `InputField()` rewrite
    - `widgets/buttons.py` module:
        + `Button`
        + `Checkbox`
        + `IconButton`
        + `LabelButton`

* later releases:
    - `Splitter` rewrite:
        + fix width issues

    - `InputField` rewrite:
        + inherit from Label, make use of its `get_lines()` line breaking
        + add `bind()` method, similarly to `WindowManager`
        + better styling, support for syntax highlights

    - Rework width & height systems
        + instead of `forced_width`, there should be a combination of an overflow & a size policy
        + overflow/expand -> current no forced width behaviour
        + overflow/clip   -> shorten lines to fit width

    - make `MarkupFormatter` more dynamic:
        + there should be a way you can incorporate depth information into a code
        + this needs parser support however
        + e.g.: `[@{30 + {depth} * 36}]this is a gradient of depth`

    - maybe make `MarkupFormatter` serializable?

    - `cmd.py` rewrite

    - add background styles

    - maybe clean up how Widget "enum" attributes are written
