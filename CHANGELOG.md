# Version 4.0.0

> Items marked in bold are API breaking changes.

## Additions
- **Introduce new `Inspector` widget and `inspect` helper function**
- Add `Container.lazy_add` method to expose `_add_widget(..., run_get_lines=False)`


## Refactors
- **Move `prettify` to new submodule `prettifiers` & improve its behaviour**
- **Move `is_interactive` under `terminal`**
- **Remove `MarkupLanguage context manager in favor of a `print` method`**
- **Refactor `MarkupLanguage.pprint`**


## Fixes
- Fix support for aliasing to an existing tag
- Fix blocking `getch` call on Windows


