This is a relatively minor release, mostly focused on the new pretty-printing functionality. I wanted to release this before the next major update, as that may take some time and these features are really useful in their own right.

## Additions
- Add `Terminal.pixel_size` attribute (6e350b182849a7ba062c97aa1a55628f5c9e78cd, ce27e3cde131e66a99085cc58ba7cf39f7bb14c8)
- Add `prettify_ansi, `pprint` and `setup_displayhook()` methods to `MarkupLanguage`` (5bdf6177b28eb7fcd6475ee1b402b6b79eb671ba)


## Bugfixes
- Fix starting state not being reverted after animation finish (#38, 135a5bf553e0281a39f8318c48cffe15198426f3)


