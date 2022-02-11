# Version v2.1.0

This update is mostly focused on bug fixes, but also has some additions. The
library should now actually install on Windows machines, which is pretty dapper.

> Items marked in bold are API breaking changes.

## Removals
- **Remove broken `SIGWINCH` monitor** (#25, #19)


## Additions
- **Add `Container.scroll` and `Container.scroll\_end` helpers** (0119e31dccb600eea8e3d6ad83114ea051316bf9)
- Add `SINGLE` box type, rename old `SINGLE` box to `ROUNDED` (5dda72793644f5144daccbc7d7772771e91afb7e)


## Fixes
- **Fix some issues with `InputField`** (0920ffc1064db262b333855a856e9ac112ba3d4f)
- **Improve how terminal resize events are handled** (7143affeeac691eeee23c130fb45686b47e2213a)
- **Fix 1 char offset in non-`Container` widget widths** (e3ac8d74bbbfb3fba9d4f87a6cd0ff7d225712d8)


