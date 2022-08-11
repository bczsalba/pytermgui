## Basics

**TIM** syntax tends to be very simple. At the base, we have the following structure:

```
[tag1 tag2 ...]My content
     ^              ^
 tag group     plain text
```

...where `tag1` & `tag2` are some valid markup tags, and `My content` is the string you want them to modify.

Tag groups are always denoted by square brackets (`[` and `]`). All text outside of a tag group is considered to be plain text.



### Nesting

When encountering nested tag groups, only the innermost one will be parsed:


```termage include=docs/src/tim/syntax_innermost.py chrome=false height=1 tabs=TIM,Output
```


### Escaping

You can escape a tag group using backslashes (`\`):


```termage include=docs/src/tim/syntax_escape.py chrome=false height=1 tabs=TIM,Output
```

!!! warning "Re-parsing escaped markup"
    
    Escaping tag groups will only be effective for the first parsing of said string. During parsing, the escaped tag group will lose the backslash to hide it from the output.


## Styles

We support all generally-supported terminal "modes":

!!! info "Resource"

    For a great overview on these styles & ANSI sequences in general, see [this gist](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797) by [Christian Petersen](https://www.cbp.io/), or this [website](https://terminalguide.namepad.de/attr/).


- **bold** (mode `1`):

    Traditionally (and on some older emulators) makes text brighter, nowadays it increases the font's weight.

- **dim** (mode `2`):

    The opposite of the traditional function behind bold, makes text a bit darker.

- **italic** (mode `3`):

    Uses the italicized font variant, which tilts each character.

- **underline** (mode `4`):

    Draws a thin line under each character.

- **blink & blink2** (mode `5` & `6`):

    Repeatedly shows and hides the characters at an internal frequency. Like HTML's `<blink>`, it seems to have fallen out of favor and is no longer supported on many terminals. Some terminal's support one, but not the other.

- **inverse** (mode `7`):

    Inverts the **function** of the foreground and background colors, i.e. the foreground color will now act on the background and vice-versa.

- **invisible** (mode `8`):

    Hides text. Not very widely supported, for some reason.

- **strikethrough** (mode `9`):

    Draws a line through each character, somewhere near the vertical middle.

- **overline** (mode `53`):

    Draws a line above each character.

```termage-svg include=docs/src/tim/syntax_modes.py
```


??? info "Implementation"
    Under the hood, these styles are set by printing a special _escape sequence_ to the terminal. These sequences are structured the following way:

    ```
    \x1b[{mode_id}m
    ```

    In effect, this means `bold` stands for `\x1b[1m`, and `inverse` for `\x1b[7m`.


## Colors

The terminal generally supports 3 color palettes

- 3 bit, or 16-color

    8 base colors (`red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white` and `black`), and high-brightness version of each, making a total of 16.

- 8-bit, or 256-color:

    256 colors, each using 8 bits of information. The standard colors make up the first 16 indices.

- 24-bit, or truecolor

    Something in the ballpark of 16.7 million colors, this set represents all colors definable by 3 8-bit (`0-255`) values, each standing for one of the `RED`, `GREEN` and `BLUE` channels.

Lucky for you, the reader, TIM exposes convenient syntax for all of these!


- **Indexed colors** (3-bit and 8-bit):

    `[{index}]`, where `index` is a number in the range `0-255`, including both ends.

- **RGB colors** (24-bit):

    `[{rrr};{ggg};{bbb}]`, where `rrr`, `ggg` and `bbb` each represent a number alike the ones indexed colors use, standing for the red, green and blue channels respectively.

- **HEX colors** (alternate representation of 24-bit):

    `[#{rr};{gg};{bb}]`, where each value represents a 3-bit number like above, as a hexadecimal value.

- **Named colors** (3-bit or 24-bit):

    `[{name}]`, where `name` is a CSS color name [known to TIM](https://github.com/bczsalba/pytermgui/blob/22327a3fb2841d9f219cc1f4784fd58029347c5d/pytermgui/color_info.py#L266):

```termage-svg title=CSS\ Colors width=60 height=49 include=docs/src/tim/syntax_css_colors.py
```

Colors, by default, will act on the foreground. This can be changed by prefixing the color markup by an at-symbol (`@`), like so:

```termage include=docs/src/tim/syntax_colors_fore_back.py height=3 chrome=false tabs=TIM,Output
```


## Clearers

After you set a style, you might want to stop it affecting text. To do so, you want to use a clearer token.

Clearer tokens are denoted with the slash (`/`) prefix, and contain the identifier they are targeting.

For example:

- To clear all attributes, including modes, colors, macros, use `/` with no identifier.
- To clear a simple terminal mode, use `/{mode}`, like `/italic`.
- To clear a color, use `/fg` for foreground colors, and `/bg` for background ones.
- To clear a [macro](markup_language#macros), use either `/!{name}`, or `/!` to clear all active macros.
- To clear a hyperlink, use `/~`.

!!! warning "Clearing specific links"

    Since the terminal only supports having one active hyperlink at a time, there is no reason to have syntax for specifically clearing a single link.



## Hyperlinks

Newer terminals allow HTML anchor-inspired hyperlinks that can be clicked and take the user to places.

!!! info "Resource"

    For information on the implementation of terminal-hyperlinks, check out this [gist](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda).

In PyTermGUI TIM, we use the syntax:

```
[~{protocol}://{uri}]
```

...where `protocol` is a data-transfer protocol supported by the client (usually `http`, `https` or `file`), and `uri` is a standard URI readable by the specified protocol.

For example:

```
This documentation is hosted as a [~https://ptg.bczsalba.com]subdomain[/~] on my [~https://bczsalba.com]website!
```

...would create markup equivalent to the HTML:

```html
This documentation is hosted as a <a href="https://ptg.bczsalba.com">subdomain</a> on my <a href="https://bczsalba.com">website!</a>
```


## Macros

!!! info

    This section details the syntax, but none of the semantics and usage tips, For a more in-depth explanation on macros, see the [macro docs](../markup_language#macros).

Macros use the syntax:

```
[!{name}({arg1}:{arg2})]
```

...or the shorthand

```
[!{name}]
```

when there are no arguments passed.

In both examples, `name` is the name the macro is defined as, and `arg1` and `arg2` are some arguments passed to it. Macro arguments are separated by colons (`:`), in order to clearly visually differentiate them from Python function calls.

