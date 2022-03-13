## [4.0.1] - 2022-03-12

### Bugfixes
- Fix broken macro call in `Markapp (524d9199a5bd026b44bb37f35f2f7cc621221c08)`
- Fix string literals not being displayed correctly in `inspect` (418812492e298f0e5fbce2122f72561afd215d10)

### Additions
- Expose `inspect-identifier` markup alias (319be785350a76ff1742002dc83820f5eb9d30ac)


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
