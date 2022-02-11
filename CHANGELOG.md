# Version 2.1.1

This release fixes various issues related to `Windows` systems. It also brought about a more logical
refactor for `WindowManager.process_input`.

> Items marked in bold are API breaking changes.

## Fixes
- Fix `CTRL_C` not being captured on Windows machines (01139633c52c07d14e15e4f1fef1ba638a06df35)
- Fix `widgets/interactive.py not being packaged` (75cebf715a74c4bba9963bc6be8d870a09f7af2c)
- Silence `keys` attribute errors (75cebf715a74c4bba9963bc6be8d870a09f7af2c)


