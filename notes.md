IN PROGRESS
-----------

* ANSI implementation
    - [ ] 16-color palette
    - [ ] 256-color palette
        + [ ] 38;5 - fg
        + [ ] 48;5 - bg

    - [ ] rgb palette
        + [ ] 38;5 - fg
        + [ ] 48;5 - bg

    - [ ] `\033[{0-9}m`
    - [ ] look into if key codes (like UP) work universally or need to be platform-specific


* classes
    - [ ] BaseElement
    - [ ] Container
        + [ ] repr
            * all line based, use `print_at()`
        + [ ] add
        + [ ] iadd
        + [ ] \_add_element

    -  Prompt
    -  Label

FINISHED
--------

* context managers
    - [x] print_at(tuple[int, int])
    - [x] alt_buffer(cursor: bool)
