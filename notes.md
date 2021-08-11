Versioning scheme
-----------------

### `major`.`minor`.`patch`

#### Before v1.0.0:
- `major`: always 0
- `minor`: feature theme
- `patch`: fixes under the same feature theme

#### After v1.0.0:
- `major`: feature theme
- `minor`: lesser additions under the same feature theme
- `patch`: fixes for `minor` versions, no new features

Planned Versions
----------------

* version 0.2.0 - The Widget update!:
    - `Splitter()` rewrite
    - `InputField()` rewrite
    - `widgets/buttons.py` module:
        + `Button`
        + `Checkbox`
        + `Dropdown`
    - reorganize `widgets/`
    - remove unnecessary widgets


Current Progress
----------------

- 0.2.0
    * [x] `widgets/buttons.py`
        + [x] `Button`
        + [x] `Checkbox`
        + [x] `Dropdown`

    * [ ] `InputField` rewrite:
        + [x] inherit from Label, make use of its `get_lines()` line breaking
        + [x] add `bind()` method, similarly to `WindowManager`
        + [x] better styling, support for syntax highlights

    * [ ] `Splitter` rewrite:
        + [ ] fix width issues
        + [ ] add support for differing heights

    * [ ] Look into removing/rewriting the various extra widgets that don't do much

    * [ ] Reorganize `widgets/`
        - `base.py`
        - `boxes.py`
        - `layout.py`
        - `styles.py`
        - `buttons.py`

- 0.3.0:
    * [ ] Rework width & height systems
        + [ ] instead of `forced_width`, there should be a combination of an overflow & a size policy
        + [ ] overflow/expand -> current no forced width behaviour
        + [ ] overflow/clip   -> shorten lines to fit width

    * [ ] look into making mouse events callback-based (see winman)
        + [ ] add support for multiple events reporting at the same time

    * [ ] Rework `Widget.click()`
        + [ ] targets should be found using `Widget.get_target()`
        + [ ] `target.click()` can then be called directly
        + [ ] add `Widget.hover(target: MouseTarget)`

    * [ ] Remove/rework focus system
        + [ ] it really only exists for `InputField`, which doesn't need it anymore
        + [ ] `Widget.selected_index` should be used instead, or there should be deeper implementation

0.4.0
    * [ ] Add color methods
        + [ ] gradient (`[<@141]`, `[<141]`, `[>@141]`, `get_gradient(including: int)`)
        + [ ] complement (`get_complement(color: int)`)

    + [ ] Add support for newlines in break_line

    * [ ] make `MarkupFormatter` more dynamic:
        + [ ] there should be a way you can incorporate depth information into a code
        + [ ] this needs parser support however
        + [ ] e.g.: `[@{30 + {depth} * 36}]this is a gradient of depth`

    * [ ] add background styles


- future *(order irrelevant)*
    + [ ] `WindowManager` tiling layout

    * [ ] maybe make `MarkupFormatter` serializable?

    * [ ] `cmd.py` rewrite

    * [ ] maybe clean up how Widget "enum" attributes are written
