We provide a growing selection of widgets you can drop straight into your projects. Looking at the `widgets` submodule's contents can help illuminate you on the exact selection, but this page describes the most commonly used ones.

## A note about `auto`

Some widgets below will have an `Auto syntax` field shown. The format shown can be used by the [auto](/reference/pytermgui/widgets/__init__#pytermgui.widgets.__init__.auto) function to generate widgets from Python datatypes. This function is conveniently called within `Container` and all its subclasses (`Splitter`, `Window`, `Collapsible` & more) to let you easily create widgets with minimal imports.

For example:

```python
from pytermgui import Container

container = Container(
    "[bold accent]This is my example",
    "",
    "[surface+1 dim italic]It is very cool, you see",
    "",
    {"My first label": ["Some button"]},
    {"My second label": [False]},
    "",
    ("Left side", "Middle", "Right side"),
    "",
    ["Submit button"]
)
```

...is functionally identical to:

```python
from pytermgui import Container, Label, Splitter, Button, Checkbox

container = Container(
    Label("[bold accent]This is my example"),
    Label(""),
    Label("[surface+1 dim italic]It is very cool, you see"),
    Label(""),
    Splitter(
        Label("My first label", parent_align=0),
        Button("Some button", parent_align=2),
    ),
    Splitter(
        Label("My second label"),
        Checkbox(),
    ),
    Label(""),
    Splitter(Label("Left side"), Label("Middle"), Label("Right side")),
    Label(""),
    Button("Submit button"),
)
```

You can use whichever you find more convenient and readable.

---

## [Label](/reference/pytermgui/widgets/base/#pytermgui.widgets.base.Label)

A simple widget meant to display text. Supports line breaking and styling using both markup and simple callables.

**Auto syntax**: `"label_value"`

**Chars**: N/A

**Styles**:

- `value`: Applies to the text within the label.

    Default: No styling.

---

## [Container](/reference/pytermgui/widgets/containers#pytermgui.widgets.containers.Container)

A widget to display other widgets, stacked vertically. It may display a box around said widgets as well, using the `border` and `corner` characters.

**Auto syntax**: N/A

**Chars**:

- `border`: A `list[str]` in the order `left, top, right, bottom` that makes up the borders of the outer box.
- `corner`: A `list[str]` in the order `top_left, top_right, bottom_right, bottom_left` that makes up the corners of the outer box.

**Styles**:

- `border`: Applies to all border characters of the outer box.

    Default: `surface`.

- `corner`: Applies to all corner characters of the outer box.

    Default: `surface`.

- `fill`: Applies to the filler characters used for padding.

    Default: `background`.

---

## [Splitter](/reference/pytermgui/widgets/containers#pytermgui.widgets.containers.Splitter)


Similar to Container, but displays widgets stacked horizontally instead. Each widget is separated by the `separator` character set.

**Auto syntax**:

- `(widget1, widget2, ...)`
- `{widget_aligned_left: widget_aligned_right)`

**Chars**:

- `separator`: The `str` used to join the contained widgets.

**Styles**:

- `separator`: Applies to the `separator` character.

    Default: `surface`.

---

## [Collapsible](/reference/pytermgui/widgets/collapsible#pytermgui.widgets.collapsible)

A widget that hides or shows whatever other widgets it is given. It will always display its "trigger", the `Button` used to collapse or expand its content.

**Auto syntax**: N/A

**Chars**: 

- See `Container`.

**Styles**:

- See `Container`.

---

## [Window](/reference/pytermgui/window_manager/window#pytermgui.window_manager.window)

An extended version of `Container`, used in the `window_manager` context.

**Auto syntax**: N/A

**Chars**:

See `Container`.

**Styles**:

Same as `Container`, but expanded with:

- `border_focused`: Analogous to `border`, but only applied when the window is focused.

    Default: `surface`.

- `corner_focused`: Analogous to `corner`, but only applied when the window is focused.

    Default: `surface`.

- `border_focused`: Analogous to `border`, but only applied when the window is **NOT** focused.

    Default: `surface-2`.

- `corner_focused`: Analogous to `corner`, but only applied when the window is **NOT** focused.

    Default: `surface-2`.

---

## [Button](/reference/pytermgui/widgets/button#pytermgui.widgets.button)


Something clickable. All widgets can be made clickable by defining an `on_click` method, but this widget looks the part as well.

**Auto syntax**:

- `["button_label", button_callback]`

**Chars**:

- `delimiter`: a `list[str]` in the order `left, right`. Each character will be placed at the respective sides of the label.

**Styles**:

> All styles here apply to the full label, including the left and right hand side delimiters.

- `label`: Applies in the normal state (e.g. no hover, click applied).

    Default: `@surface dim`.

- `highlight`: Applies when the button is interacted with.

    Default: `@surface+1 dim`.


---

## [KeyboardButton](/reference/pytermgui/widgets/keyboard_button#pytermgui.widgets.keyboard_button)



Much like button, but has a default binding applied to it. This binding is also reflected in its label.

**Auto syntax**: N/A

**Chars**:

- All `Button` chars
- `bracket`: Used to wrap the button's bound key.

**Styles**:

- See `Button`.


---


## [Checkbox](/reference/pytermgui/widgets/checkbox#pytermgui.widgets.checkbox)

A simple check box, you know the drill.

**Auto syntax**: 

- `[bool_default, callback_method]`

**Chars**:

- `delimiter`: Wraps the checkbox's value
- `checked`: The character inserted between delimiters when the widget is checked.
- `unchecked`: The character inserted between delimiters when the widget is **un**checked.


**Styles**:

- See `Button`.


---

## [Toggle](/reference/pytermgui/widgets/toggle#pytermgui.widgets.toggle)

A button that toggles its label between the two given values.

**Auto syntax**:

- `[("label_1", "label_2"), callback_method]`

**Chars**:

- See `Button`.

**Styles**:

- See `Button`.

---

## [Slider](/reference/pytermgui/widgets/slider#pytermgui.widgets.slider.Slider)

A widget to display and/or control a floating point value.

**Auto syntax**: N/A

**Chars**:

- `cursor`: The character placed at the end of the filled section. If nothing is given, `rail` is used.
- `rail`: Used to fill up the width of the slider, colored as applicable.
- `delimiter`: Wraps the `rail` characters on both sides.

**Styles**:

- `cursor`: Applied to the `cursor` character, or the last character of the rail.

    Default: `primary`.

- `filled`: Applied to the filled section of the rail if the slider is **not** selected.

    Default: `surface+1`.

- `filled_selected`: Applied to the filled section of the rail if the slider is selected.

    Default: `primary`.

- `unfilled`: Applied to the unfilled section of the rail if the slider is **not** selected.

    Default: `surface-1`.

- `unfilled_selected`: Applied to the unfilled section of the rail if the slider is selected.

    Default: `surface`.

---

## [InputField](/reference/pytermgui/widgets/input_field#pytermgui.widgets.input_field.InputField)

A field to display input. Should be used in a context that sends it keyboard inputs, such as `WindowManager`.

**Auto syntax**: N/A

**Chars**: N/A

**Styles**:

- `value`: Applies to the text of the input field.

    Default: No styling.

- `prompt`: Applies to the string displayed before the field's value, controlled by the `prompt` parameter.

    Default: `surface+2`

- `cursor`: Applies to the field's cursor.

    Default: `@primary dim #auto`

---

## [PixelMatrix](/reference/pytermgui/widgets/pixel_matrix#pytermgui.widgets.pixel_matrix.PixelMatrix)

A customizable matrix of unicode pixels. With some image decoding, it can be used to display low-resolution pictures.

**Auto syntax**: N/A

**Chars**: N/A

**Styles**: N/A

---

## [DensePixelMatrix](/reference/pytermgui/widgets/pixel_matrix/#pytermgui.widgets.pixel_matrix.DensePixelMatrix)

Similar to `PixelMatrix`, but instead of using two unicode block characters per pixel, it uses either the upper or lower half of one. Allows for higher resolution pictures!

**Auto syntax**: N/A

**Chars**: See `PixelMatrix`

**Styles**: See `PixelMatrix`



