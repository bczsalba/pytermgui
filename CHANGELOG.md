This version mostly focused on adding some nice utilities while improving the old ones.

Things to point out:
- Improvements to pretty printing in general
- `pretty` module: This is a very simple module that allows setting up displayhook with only one line in the REPL
- `KeyboardButton` widget: This allows keyboard mnemonics inside PTG.
- `!rainbow` and `!gradient` macros: These are very pretty and fancy looking.

## Refactors
- Colorize version info (b3075a3b6b4ef481e4c5353ce523f806ec9376ce)
- Stop displaying version hash info if it could not be found (695511610df6dce9c18bb7e105422d0dbd304b72)
- Improve `parser documentation` (933729e98142039ae601bc3eecebfb60e39882db)
- Extend pretty printing to more data types (d0ae9ccbb4a7c5130f55751036e02d3a9e5b606a)
- Improve `IPython` display hook support (caa7c748f51019166b01ea163cb6d2f77fb537b5)


## Bugfixes
- Fix redundant sequence output in `MarkupLanguage.parse` (7f49087a747fb3d7189f09a598c29313c340e1cc)
- Fix markup macros only running once due to caching (a2edf6da110bc229e423793fed2153f6b911cb3e)
- Fix Window.`is_modal` not being applied properly since a mouse handling refactor (c1d36190d20cbcefcae8c91181d2d2d4de37c269)


## Additions
- Add `KeyboardButton` widget (a1a0dadfb6243981c2a7bdd4f57048a87c41bef0, c495dd0d4d6a173a2ad9e031d003a17eb080123d)
- Add `non_first_padding` to `Label` (c630e6f9aff2dbc688197ab9866657ef04d70f8b)
- Add ability to set `box` in `Container` constructor (88536be5035e83ed7ad4c4b2de4980bd2c85a559)
- Add `pretty` module for quick displayhook setup (48fb0dfde9742328603e26950deca657ad483299)
- Add `!rainbow` and `!gradient` macros (bc0e0911a14922111a429aa153e4ebc8ff4aa394)


