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

- 1.0.0 - First stable release!
    * [ ] Fix macro only running once
    * [ ] Fix `SIGWINCH` handling (see GH issue)

    * [x] Rework `Widget.click()`
        + [x] targets should be found using `Widget.get_target()`
        + [x] **MouseEvent should be sent to the widget-specific mouse handler.**
            - [x] `Widget.handle_mouse(event: MouseEvent, target: Optional[MouseTarget]) -> bool`
            - [x] This method can then split off into various handlers for all actions

    * [x] Rewrite `WindowManager`
        + The current implementation is old and rushed, with a lot of shortcuts.

    * [x] Add `handle_mouse` method to `Widget`
    * [x] Add `handle_key` method to `Widget`

    * [ ] Rework width & height systems
        + [x] instead of `forced_width`, there should be a combination of an overflow & a size policy
        + [x] overflow/expand -> current no forced width behaviour
        + [x] overflow/clip   -> shorten lines to fit width
	+ [ ] some kind of measurement system:
		- `Widget.measurements` property: `(min, max)`

    * [ ] Fix long-standing issues
    	+ [x] inner-container mouse selection is buggy
	+ [-] `cmd` helper menu is broken -- problem temporarily ignored
	+ [ ] inner-container keyboard selection ends outer container
	+ [ ] `Container` and `WindowManager` both resize `Window` on `SIGWINCH`

* [x] Add JSON config parsing
* [ ] add background styles

Future versions
---------------

- 2.0.0 - The stylish update!
    * [ ] Add color methods
        + [ ] gradient (`[<@141]`, `[<141]`, `[>@141]`, `get_gradient(including: int)`)
        + [ ] complement (`get_complement(color: int)`)

    + [ ] Add support for newlines in break_line

    * [ ] make `MarkupFormatter` more dynamic:
        + [ ] there should be a way you can incorporate depth information into a code
        + [ ] this needs parser support however
        + [ ] e.g.: `[@{30 + {depth} * 36}]this is a gradient of depth`

- unnamed *(order irrelevant)*
    + [ ] `WindowManager` tiling layout

    * [ ] maybe make `MarkupFormatter` serializable?

    * [ ] maybe clean up how Widget "enum" attributes are written
