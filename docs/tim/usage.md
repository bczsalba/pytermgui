So the things you read before are all great and all, but where do you apply them? Glad you (definitely) asked!

The [markup](/reference/pytermgui/markup) module exports the `tim` name; this is an instance of [MarkupLanguage](/reference/pytermgui/markup/language#pytermgui.markup.language.MarkupLanguage). `tim` is going to be your best pal for handling anything related to TIM parsing.

??? info "Why do we use classes to represent a static language?"

    There are a couple of aspects of TIM that require keeping track of some 'state', e.g. aliases and macros. This state, referred to as `context` internally, is passed in to all parsing functions to provide the data needed to apply the non-built-in tags.

    `MarkupLanguage` keeps track of some context that can be modified with the `alias` and `define` methods, and passes this state into every `parse*` call for you!

**Fun fact**: You can use TIM in most widgets! See the [styling docs](/widgets/styling) for more info.

## Methods

### Parse

The most important method to know about is [parse](/reference/pytermgui/markup/language#pytermgui.markup.language.MarkupLanguage.parse). It takes some TIM string, and returns formatted text to display in the terminal.

```termage height=5 include=docs/src/tim/usage_parse.py
```

### Print

Since calling `print` on parsed text _every time_ can get a bit repetitive, we have a helper function to do it for you! Just call [print](/reference/pytermgui/markup/language#pytermgui.markup.MarkupLanguage.print) with the same positional and keyword arguments as you would use for the builtin print, and see the magic!

You can print non-TIM text with this method as well, but you might wanna use the [escape](/reference/pytermgui/markup/language#pytermgui.markup.language.escape) function if you want to make sure to keep things from being parsed. <sub>Though at that point, you might as well use the builtin print!</sub>

```termage height=5 include=docs/src/tim/usage_print.py
```

### Alias

As mentioned above, you can modify the TIM parser's state to enable custom behaviour. The first of these is aliasing tags, which essentially makes one tag expand to any other groups of tags while parsing.

!!! warning
    Alias tags are detected as tags that had no previous meaning, e.g. aren't included in the builtin tags and are not macros. At the moment it is not possible to re-define tags.

```termage height=5 include=docs/src/tim/usage_alias.py
```

### Define

You can also define macros using the [define](/reference/pytermgui/markup/language#pytermgui.markup.language.define) method. Macros are Python functions you can call from TIM to transform your text. They can **only** be referenced from TIM, definition must come from the outer Python context.

There are a couple of simple macros defined by default, such as `!upper`, `!capitalize` and `!lower`. These are all tied to the respective Python `str` methods.

```termage height=5 include=docs/src/tim/usage_define1.py
```

A favored example of mine is creating a simple localization layer for your application. You can define a macro, `!lang`, that is given a localization-id and returns some localized text. This can then be used in any place that TIM is accepted, since it is defined on the global instance.

```termage height=7 include=docs/src/tim/usage_define2.py
```
