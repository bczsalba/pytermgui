Current Progress
----------------

* version 0.1.4 - Significantly better syntax:
    - [x] Magic type conversion for `Container`
    - [x] Arbitrary attribute setting in any `Widget` construction

    - [x] Various improvements to the `window_manager` module
        + `WindowManager.bind()`
        + `WindowManager.run()` rewrite
        + Performance & usability improvements

    - [x] Various improvements to `Button`
        + More button-like style
        + New padding attribute

    - [x] Various improvements to `MouseTarget`
        + Fix right offset
        + Better handling by parent objects

    - [x] Better performance
        + Fix infinite `Container()` mouse_target additions

* version 0.2.0 - The Widget update!:
    - change to semantic versioning?
    - `Splitter()` rewrite
    - `InputField()` rewrite
    - `widgets/buttons.py` module:
        + `Button`
        + `Checkbox`
        + `IconButton`
        + `LabelButton`
        + `Dropdown`

* later releases:
    - `Splitter` rewrite:
        + fix width issues

    - look into making mouse events callback-based (see winman)

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
