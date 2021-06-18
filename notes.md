IN PROGRESS
-----------

* later releases:
    - `Splitter` rewrite:
        + inherit from `Container`
        + better spacing (obv)
        + fix `selectables_length`

    - make `MarkupFormatStyle` more dynamic:
        + there should be a way you can incorporate depth information into a code
        + this needs parser support however
        + e.g.: `[{{30 + {depth} * 36 }}]this is a gradient of depth[/]`

    - maybe make `MarkupFormatStyle` serializable?

    - `cmd.py` rewrite

    - `Container.get_lines()` method rethink:
        + make it less messy
        + the parent `Container` should send the object an available width & height
        + add size policies
        + while we're at it, the current handling for enums is kinda messy:
            * you set `VERT` & `HORIZ` align as an attribute, but you call a setter with `CENTER`

    - add a syntax style for `InputField`

    - add background styles

    - maybe clean up how Widget "enum" attributes are written
