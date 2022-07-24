## [7.0.0] - 2022-07-24

### Additions

- Support CSS color names in TIM code
- Support terminal resize events on Windows (@Tired-Fox)
- Add `ignore_any` parameter to `Widget.execute_binding`

### Bugfixes

- Fix `InputField` handling clicks & drags started outside of it
- Fix `CTRL_C` not killing compositor thread by making it a daemon
- Fix contents of `widget.positioned_line_buffer` being duplicated before and
  after vertical alignment

### Refactors

- **Rewrite of the TIM engine (now at version 3!)**
- **Move TIM highlighting from an instance method to a highlighter**
- Move to `pyproject.toml`-based builds
- Stop relying on `visibility=hidden` in SVG exports

### Removals

- **Remove `get_applied_sequences` helper function**


## [6.4.0] - 2022-06-14

### Additions

- Add hover highlighting for `Button`

### Bugfixes

- Fix Splitters only sending mouse events on the first row of height

### Refactors

- Implement semantic mouse handlers
- Improve mouse input cascade logic


## [6.3.0] - 2022-06-05

### Refactors

- Refactor `InputField`
- Start caching `Token.sequence` to improve performance
- Start lazy-evaluating terminal resolution

### Bugfixes

- Use `SVG` export prefix as the class of the `text` elements
- Fix `Inspector` not resizing to custom global terminals

### Additions

- Add `break_line` `fill` argument
- Add `chrome` SVG argument


## [6.2.2] - 2022-05-26

### Bugfixes

- Fix text being misaligned in both Firefox and Safari

### Refactors

- Reduce redundancy in SVG export dimensions

## [6.2.1] - 2022-05-25

### Bugfixes

- Fix `\n` being escaped when highlighting python

### Refactors

- Add `WindowManager.autorun` class attribute


## [6.2.0] - 2022-05-24

### Bugfixes

- Fix `StandardColor` HEX and RGB being indexed from the wrong pool
- Fix overly greedy ~~yeeting~~ optimization of `ttype=POSITION` tokens
- Fix `ttype=POSITION` tokens acting unpredictably when multiple were present in a string

### Additions

- Add `WindowManager.autorun` attribute

### Refactors

- Implement usage of SVG tags when exporting


## [6.1.0] - 2022-05-17

### Additions

- Introduce `__fancy_repr__` protocol
- Add `Color` format specifiers
- Add `Animation.pause` & `Animation.unpause`

### Bugfixes

- Fix scrolled widgets not getting positioned correctly
- Fix an issue with 2-bit colors being interpreted as 8-bit ones

### Refactors

- Improve `highlight_python` vs string


## [6.0.0] - 2022-05-12

### Removals

- **Remove `Window.allow_fullscreen`, `Window.toggle_fullscreen`**

### Refactors

- **Add new, customizable window blur styles**
- **Rename all builtin aliases to follow the `domain.item` naming scheme**
- Implement a new, much faster and `\n` supporting `break_line` function
- Improve animation stability
- Start caching `real_length`, `strip_markup` & `strip_ansi` results
- Refactor `StyledText` to only tokenize on-demand
- Rewrite the pattern used to match markup to improve how escapes are handled
- Introduce new, layout based CLI with an RGB colorpicker & inspector

### Additions

- Add `Collapsible` widget (114da3a3d769d6abd72a8727ed036b1e947c0a23)
- Add new `highlighters` module with `RegexHighlighter` class
- Add `is_scroll, `is_primary`&`is_secondary` helpers to MouseEvent`
- Add `Terminal.no_record` context
- Add `WindowManager.alert` and `WindowManager.float` methods
- Add layout `assign` parameter to `WindowManager.add`
- Add window manager `Layout` class

### Bugfixes

- Fix overly greedy optimization in `MarkupLanguage.parse` getting rid of important unsetters
- Fix `/` not being handled properly in various places


## [5.0.0] - 2022-04-19

### Refactors

- **Refactor `window_manager.py` into 3 files under `window_manager` submodule**
- **Refactor the entire animation system**
- Move scrolling behaviour into new `ScrollableWidget` class
- Improve `Terminal` API
- Rename `widgets/layouts` → `widgets/containers`

### Additions

- Add `StyleManager.__call__` method that sets the given \*\*kwargs keys and values
- Add (currently unused) `Widget.get_change` helper


## [4.3.2] - 2022-04-09

### Bugfixes

- Improve how pixel size is received and fix process hanging when the terminal does not support it
- Fix stream truncation raising an error on Windows

### Additions

- Add `getch_timeout` method


## [4.3.1] - 2022-04-03

### Bugfixes

- Fix #45 by catching `errno.EINVAL` on stream truncation
- Fix `Container` first lines sometimes having wrong indentations in SVG exports
- Fix `Helpers` app not showing any bindings


## [4.3.0] - 2022-04-02

### Additions

- Re-introduce `Helpers` ptg app
- Add F-keys to `input.keys`
- Add `terminal` `Recorder` class, ability to record anything written to the terminal using a context
- Add `Color.hex` property
- Add `Color` default fore & background setter and getters, using the terminal’s palette
- Add `LINK` and `POSITION` `TIM` token types
- Add `exporters` module to generate HTML pages and SVG screenshots from any terminal content
- Add `style` construction argument to `Label`
- Add `tim.get_styled_plains` method

### Refactors

- Slightly optimize how `WindowManager.print` works
- Move regex-related utilities into `regex.py`


## [4.2.1] - 2022-03-22

### Refactors

- Improve color degradation & caching


## [4.2.0] - 2022-03-21

### Additions

- Add a graceful degradation `Color` layer
- Expose color support in `terminal`
- Add support for prettifying `UserDict` and `UserList`
- Add support for `NO_COLOR` using greyscale ramps
- Add `colors` module with color types for all terminal colors

### Refactors

- Move `terminal` to its own module

### Bugfixes

- Fix `[` sometimes being ommitted during `prettify_markup`


## [4.1.0] - 2022-03-16

### Refactors

- Implement new `StyleManager` class & API
- Improve `Container.debug` to shorten itself & use `type(self)`

### Additions

- Add value readout to `ptg -g`

### Bugfixes

- Fix `ESC` not being outputted in `ptg -g`


## [4.0.1] - 2022-03-12

### Bugfixes

- Fix broken macro call in `Markapp`
- Fix string literals not being displayed correctly in `inspect`

### Additions

- Expose `inspect-identifier` markup alias


## [4.0.0] - 2022-03-12

### Additions

- **Introduce new `Inspector` widget and `inspect` helper function**
- Add `Container.lazy_add` method to expose `_add_widget(..., run_get_lines=False)`

### Refactors

- **Move `prettify` to new submodule `prettifiers` & improve its behaviour**
- **Move `is_interactive` under `terminal`**
- **Remove `MarkupLanguage context manager in favor of a `print` method`**
- **Refactor `MarkupLanguage.pprint`**

### Bugfixes

- Fix support for aliasing to an existing tag
- Fix blocking `getch` call on Windows


[7.0.0]: https://github.com/bczsalba/pytermgui/compare/6.4.0...7.0.0
[6.4.0]: https://github.com/bczsalba/pytermgui/compare/6.0.0...6.4.0
[6.3.0]: https://github.com/bczsalba/pytermgui/compare/6.2.2...6.3.0
[6.2.2]: https://github.com/bczsalba/pytermgui/compare/6.2.1...6.2.2
[6.2.1]: https://github.com/bczsalba/pytermgui/compare/6.2.0...6.2.1
[6.2.0]: https://github.com/bczsalba/pytermgui/compare/6.1.0...6.2.0
[6.1.0]: https://github.com/bczsalba/pytermgui/compare/6.0.0...6.1.0
[6.0.0]: https://github.com/bczsalba/pytermgui/compare/5.0.0...6.0.0
[5.0.0]: https://github.com/bczsalba/pytermgui/compare/4.3.2...5.0.0
[4.3.2]: https://github.com/bczsalba/pytermgui/compare/4.3.1...4.3.2
[4.3.1]: https://github.com/bczsalba/pytermgui/compare/4.3.0...4.3.1
[4.3.0]: https://github.com/bczsalba/pytermgui/compare/4.2.0...4.3.0
[4.2.1]: https://github.com/bczsalba/pytermgui/compare/4.2.0...4.2.1
[4.2.0]: https://github.com/bczsalba/pytermgui/compare/4.1.0...4.2.0
[4.1.0]: https://github.com/bczsalba/pytermgui/compare/4.0.0...4.1.0
[4.0.1]: https://github.com/bczsalba/pytermgui/compare/4.0.0...4.0.1
[4.0.0]: https://github.com/bczsalba/pytermgui/compare/3.2.1...4.0.0
