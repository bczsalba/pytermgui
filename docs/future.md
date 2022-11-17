# The future of this library

I intend on growing this library as long as there are ways to improve it; life might get in the way at some points, but I want to keep using the project in my personal tooling, and I know many people count on it's reliability for their own.

The current version of the module is pretty stable in terms of the API. There is only a handful of upcoming API changes, some of which will unfortunately have to roll over a major version. This page exists as a sort of heads-up note, so users know what to expect. I will try to keep this up to date whenever plans change, or tasks are complete.


## **8.0.0** - The _(second)_ widget update

The next major release is, according to my plans, the last one for a long time. It will be a modernization of a lot of APIs, and it's main purpose is to bundle all the minor but compatibility breaking changes together into a single release.

The end goal of this version is to make it so implementing the [7GUIs](https://eugenkiss.github.io/7guis/) is simple, and can be done by most newcomers to the library.

### Planned changes

- A new, more stable `Container.get_lines` implementation
- Better API for aligning widgets within containers
- A rethink of the sizing system -- likely implementing the layout system's [dimensions](/reference/pytermgui/window_manager/layouts#pytermgui.window_manager.layouts.Dimension), and possibly removing static sizes
- Better implementation of heights, one that is more consistent with widths
- Better buttons: checkboxes with labels, new base button class with more customization and nicer styling and rethink of toggle
- Better, more customizable layouts within containers: probably a better splitter, possibly allowing Containers to use [layouts](/reference/pytermgui/window_manager/layouts#pytermgui.window_manager.layouts.Layout)


## **8.1.0** - A better YAML styling engine

The current YAML styling works, but doesn't support quite as much as I would like it to. CSS, as <sub>as hideous as it can be</sub> does some things well: being able to apply styles to specific elements individually, swapping style groups on the fly and integration with the scripting language, just to name a few.

With this update, our YAML files should do more or less the same as CSS, but in a more thought-out manner, with clear and readable syntax.

An example PTG YAML file could be the following:

```yaml title="styles.ptg"
aliases:
  main-background: '@surface-1'
  main-foreground: 'surface+1'

config:
  *:
    background: 'main-background'

  Window is_modal?:
    borders: 'DOUBLE'
    styles.border__corner: 'error'

  Button .confirm:
    styles.normal:
      background: '@success-2'
      foreground: 'success'

    styles.hover:
      background: '@success'
      foreground: 'success+1'

    styles.active:
      background: '@success+1'
      foreground: 'success+2'
```

```python
from pytermgui import Stylesheet

styles = Stylesheet.load("styles.ptg", auto_reload=True)
```

### Planned changes

- Re-wiring `_IdManager` to act as the style managment overlord
- Likely re-writing the `file_loaders` module. I hope to keep the current API alive, with massive deprecation notices
- Moving some of the default widget configuration into a `default.yaml` file


## **8.X.0**: A better composition

The current compositor isn't super smart. It does _way_ too much writes to the terminal, and thus it makes things flickery and unstable on lower power emulators. A fix to this is already far in the works, and involves a resizable matrix of screen coordinates to their content. I want this update to happen seemlessly on the user's side, but this makes things a _lot_ more difficult.

### Planned changes

- Add a canvas class that handles emulating the terminal's display
- Change compositor to write to a canvas, and to only update the terminal with the canvas' contents
