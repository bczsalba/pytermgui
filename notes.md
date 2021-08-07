Versioning method
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
    - change to semantic versioning?
    - `Splitter()` rewrite
    - `InputField()` rewrite
    - `widgets/buttons.py` module:
        + `Button`
        + `Checkbox`
        + `Dropdown`
    - `widgets/` reorginization


Current Progress
----------------

- 0.2.0
    * [ ] `widgets/buttons.py`
        + [x] `Button`
        + [x] `Checkbox`
        + [x] `Dropdown`

    * [ ] `InputField` rewrite:
        + [ ] inherit from Label, make use of its `get_lines()` line breaking
        + [ ] add `bind()` method, similarly to `WindowManager`
        + [ ] better styling, support for syntax highlights

    * [ ] `Splitter` rewrite:
        + [ ] fix width issues
        + [ ] add support for differing heights

    * [ ] Reorganize `widgets/`
        - `base.py`
        - `boxes.py`
        - `layout.py`
        - `styles.py`
        - `buttons.py`

- future
    * [ ] look into making mouse events callback-based (see winman)

    * [ ] Rework width & height systems
        + [ ] instead of `forced_width`, there should be a combination of an overflow & a size policy
        + [ ] overflow/expand -> current no forced width behaviour
        + [ ] overflow/clip   -> shorten lines to fit width

    * [ ] make `MarkupFormatter` more dynamic:
        + [ ] there should be a way you can incorporate depth information into a code
        + [ ] this needs parser support however
        + [ ] e.g.: `[@{30 + {depth} * 36}]this is a gradient of depth`

    * [ ] maybe make `MarkupFormatter` serializable?

    * [ ] `cmd.py` rewrite

    * [ ] add background styles

    * [ ] maybe clean up how Widget "enum" attributes are written
