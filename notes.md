IN PROGRESS
-----------

* 0.1.0 release:
    - [x] fix whatever is going wrong with `--markup` SyntaxErrors
    - [ ] `ListView` should have a construction-parameter similar to `Prompt`'s highlight_target
    - [ ] fix `InputField` up & down

* later releases:
    - `cmd.py` rewrite

    - `Splitter` rewrite:
        + inherit from `Container`
        + better spacing (obv)
        + fix `selectables_length`

    - `Container.get_lines()` method rethink:
        + make it less messy
        + the parent `Container` should send the object an available width & height
        + add size policies
        + while we're at it, the current handling for enums is kinda messy:
            * you set `VERT` & `HORIZ` align as an attribute, but you call a setter with `CENTER`

    - add a syntax style for `InputField`

    - add background styles

    - maybe clean up how Widget "enum" attributes are written
