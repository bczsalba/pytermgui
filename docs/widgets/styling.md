All built in widgets use a central color [palette](/reference/pytermgui/palettes/#pytermgui.palettes.Palette), referencable within [TIM](/tim) code. Each widget will use appropriate shades of the palette by default.

Since this palette is defined globally, you can also re-generate it with new colors. It only requires a primary color, but you may give it as many as you please.

Here is the default palette:

```termage-svg width=91 height=44 title=pytermgui/palettes.py
from pytermgui import palette
palette.print()
```

As you can see, each color name has a set of negatively and positively shaded variants. These can be accessed in the format: `{color_name}{shade_offset}`, such as `primary+2` or `surface2-1`. The "main" color can be referred to without an offset, like `accent` or `success`. 

Each color also has a background variant assigned to it, which may be used by prefixing the color-of-interest by an at symbol (`@`), like `@error` or `@secondary+3`.

!!! warning

    Since the underlying colors _may_ change between runs, it's best to make sure contrast ratios are met at all times. This is possible in PTG using the `#auto` markup pseudo-tag.

    As mentioned later, the library will try to append this tag to any widget style without a set foreground color. To use it outside of a widget (or to make absolute certain that it applies), add it to your markup:

    ```termage chrome=false height=2
    from pytermgui import tim

    tim.alias_multiple(**{"@my-surface1": "@white", "@my-surface2": "@black"})
    tim.print("[@my-surface1 #auto] Black on white [@my-surface2 #auto] White on black ")
    ```


## Styling widgets

As mentioned above, all widgets come with a basic, aesthetically pleasing set of styles. Sometimes though, you might wanna get a fresher look.


### Modifying the palette

The easiest way to change up the look of your apps is by manipulating the global palette. This will change the colors of all built-in widgets, and all custom ones (so long as they use the palette colors).

This can be done using the [Palette.regenerate](/reference/pytermgui/palettes/#pytermgui.palettes.Palette.regenerate) method:

```python
from pytermgui import palette

palette.regenerate(primary="skyblue")
```

Under the hood, it will look at the given color, and generate some complementaries for it. 

The above code gives use the following palette, by the way:

```termage-svg width=91 height=44 title= 
from pytermgui import palette

palette.regenerate(primary="skyblue").print()
```

!!! note
    Using highly saturated colors as for the primary color will likely result in harsh looking styles. Even if you are tied to a certain neon-looking HEX color, it is usually nicer to use some toned-down version of it as the primary, and possibly including it as the `secondary`, `tertiary` or `accent` arguments.


### Modifying styles

If just changing the base colors isn't enough, you can add more involved styles on a per-widget basis. 

Assigning styles is done through each widget's [StyleManager](/reference/pytermgui/widgets/styles/#pytermgui.widgets.styles.StyleManager), which can be accessed using `widget.styles`.

Properties can be set in a couple of ways. The simplest one uses the dot syntax:

```python
widget.styles.label = my_style
```

You may also assign styles in the same statement as a widget's creation if you are pressed on space, by calling the `styles` property with a set of keyword arguments:

```python
widget = MyWidget().style(label=my_style)
```

Finally, it is possible to assign multiple styles to the same value in one statement. This can be done by separating each key with 2 underscore characters, and works for either of the above methods:

```python
widget.styles.border__corner = my_border_style
widget2 = MyWidget().styles(border__corner=my_border_style)
```

All the above examples modify styles pre-defined by the widget at declaration time. To see all the built-in styles, see the section on [built-in widgets](/widgets/builtins).

Values for these calls can be of 2 general types:


#### TIM string shorthands

The easier way to create custom styles is by defining some markup for them. A fully expanded markup string contains both the `{depth}` and `{item}` template keys, but it can be shortened and [expanded automatically](/reference/pytermgui/widgets/styles/#pytermgui.widgets.styles.StyleManager.expand_shorthand) for convenience.

`item` must be in the final style string. It represents the string that was passed for styling. `depth` is not necessary to use; it represents the given widget's `depth` property.

For example, `surface+2 italic dim` would be expanded into `[surface+2 italic dim]{item}`, while `[!gradient(210) bold]{item}` would remain untouched.

!!! info
    Under the hood, these strings will create [MarkupFormatter](/reference/pytermgui/widgets/styles/#pytermgui.widgets.styles.MarkupFormatter) instances, which perform the formatting and parsing when called.

    TL;DR: This method is only syntactic sugar over the one below.


#### Custom callables

For more granular control of a style, one may use a callable. These follow the following signature:

```python
def my_style(depth: int, item: str) -> str:
```

...where `depth` is an integer related to the styled widget, and `item` is the text in need of styling. The return of this is always assumed to be parsed, ANSI-coded text.

This method is far more powerful than just using template string, but it's also a lot more noisy to write. Here is a cool button style:

```python
--8<-- "docs/src/widgets/style_callables.py"
```

This gives the following result. See the `#auto` tag setting valid foregrounds for both light and dark backgrounds:

```termage-svg include=docs/src/widgets/style_callables.py title=docs/src/widgets/style_callables.py height=5
```
