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

Upcoming Version
----------------

- 0.3.0 - Mark(up) of the Snake!
    * [x] Markup language Instances
    * [x] (maybe) better macro arguments (`[!align(30, center)]text`)
    * [x] Caching system
    * [x] Capture `signal.WINCH`, use it for window size detection
    * [x] Remove/rework focus system
        + [x] it really only exists for `InputField`, which doesn't need it anymore
        + [x] `Widget.selected_index` should be used instead, or there should be deeper implementation


Future versions
---------------

- 1.0.0 - First stable release!
    * [ ] Rework `Widget.click()`
        + [ ] targets should be found using `Widget.get_target()`
        + [ ] **MouseEvent should be sent to the widget-specific mouse handler.**
            - [ ] `Widget.handle_mouse(event: MouseEvent) -> bool`
            - [ ] This method can then split off into various handlers for all actions

    * [ ] Rework width & height systems
        + [ ] instead of `forced_width`, there should be a combination of an overflow & a size policy
        + [ ] overflow/expand -> current no forced width behaviour
        + [ ] overflow/clip   -> shorten lines to fit width

- 2.0.0 - The stylish update!
    * [ ] Add color methods
        + [ ] gradient (`[<@141]`, `[<141]`, `[>@141]`, `get_gradient(including: int)`)
        + [ ] complement (`get_complement(color: int)`)

    + [ ] Add support for newlines in break_line

    * [ ] make `MarkupFormatter` more dynamic:
        + [ ] there should be a way you can incorporate depth information into a code
        + [ ] this needs parser support however
        + [ ] e.g.: `[@{30 + {depth} * 36}]this is a gradient of depth`

    * [ ] add background styles


- unnamed *(order irrelevant)*
    + [ ] `WindowManager` tiling layout

    * [ ] maybe make `MarkupFormatter` serializable?

    * [ ] maybe clean up how Widget "enum" attributes are written
