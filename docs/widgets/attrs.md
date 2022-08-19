All widgets share a set of attributes that can be used to make things look the way you want. Here is a quick overview on them.

!!! note

    This API will likely be reformed in the future to be properly controllable through YAML config files. The underlying attributes will remain the same, but the way to access/modify them will be improved.

## Applicable to all

### Parent align

This attribute can be used to tell a widget's parent to align it left, right or center.

Possible values:

- `HorizontalAlignment.LEFT` or `0`: Aligns to the left side.
- `HorizontalAlignment.CENTER` or `1`: Aligns to the center.
- `HorizontalAlignment.RIGHT` or `2`: Aligns to the right.

Default: `HorizontalAlignment.CENTER`

```termage include=docs/src/widgets/attrs/parent_align.py width=60 height=10
```

### Size policy

Widget width adjustments are handled through a system of policies. The basics are:

- `SizePolicy.FILL`: The widget will take up the entire width provided by its parent.
- `SizePolicy.STATIC`: The widget will remain at a certain width, and its parent will never try to resize it.
- `SizePolicy.RELATIVE`: The widget will take up a certain percentage of its parent's width, denoted by a floating point value between 0 and 1. 

While you _can_ set these manually, it's easier for the both of us if you use the helper properties instead:

<p style="padding-top: 5px"></p>

```termage-svg chrome=false height=23 title="Size policy helpers"
from pytermgui import inspect, Widget
print(inspect(Widget.static_width.fget, show_header=False))
print("\n")
print(inspect(Widget.relative_width.fget, show_header=False))
```

Default: `SizePolicy.FILL`

!!! warning

    `SizePolicy.STATIC` can cause various issues if the parent widget doesn't have enough width available. If using it, _make sure to make sure_ that the parent will never be smaller than the given widget!

```termage include=docs/src/widgets/attrs/size_policy.py width=60
```

## Applicable to Container

### Box

The container `border` and `corner` characters can be set to a few presets, which are defined in the [boxes](/reference/pytermgui/widgets/boxes) module. 

Setting the `box` attribute to either a `Box` instance or an upper-cased box name will set both the `border` and `corner` characters to those defined by the box.

Default: `SINGLE` for `Container`, `DOUBLE` for `Window`.

```termage include=docs/src/widgets/attrs/box.py height=80
```

## Applicable to Window

!!! note
    
    Container's [attributes](#applicable-to-container) also apply to Window.


### Title

Windows can display text on the top-left corner of their borders.

!!! warning

    You can only use markup in titles if the given window's `corner_style` parses TIM. This will always be the case with string-based shorthand styles, but may not be for custom callables. See the [styling](/widgets/styling#modifying-styles) section for more info!

Default: `""`

```termage include=docs/src/widgets/attrs/title.py
```
