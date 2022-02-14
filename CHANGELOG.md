# Version 2.2.0

> Items marked in bold are API breaking changes.

## Refactors
- Make `Container.\_centered\_axis` public (0304aca4b94517648b46bcf68e3ae4a18f1e0b68)
    * Note: This is not deemed API breaking, as this attribute was never meant to be
user facing.


## Fixes
- Fix `Overflow.HIDE` only hiding entire widgets (4289a5c6bd5df535a43053173179bc9f3ec0526f)
- Fix `getch` application growing in height indefinitely (ea5b721248f6c599a6c795a34bd1dae5608eb565)


## Additions
- Add Animator class (c87586f40bafcd88c557abd41691c898bb74caaa, ceb030d96269ebf8a8898c8969df13a85ac55704)


