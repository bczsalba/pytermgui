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



[4.2.0]: https://github.com/bczsalba/pytermgui/compare/4.1.0...4.2.0
[4.1.0]: https://github.com/bczsalba/pytermgui/compare/4.0.0...4.1.0
[4.0.1]: https://github.com/bczsalba/pytermgui/compare/4.0.0...4.0.1
[4.0.0]: https://github.com/bczsalba/pytermgui/compare/3.2.1...4.0.0
