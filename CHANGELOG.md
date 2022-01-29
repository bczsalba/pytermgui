# Version 2.0.0

This version contains a whole lot of nice Quality of Life changes, as well as some major additions. The highlights would probably go to `Container`-s now having native support for scrolling their contents, a brand-spanking new and hugely improve mouse input API, and improved documentation.

> Items marked in bold are API breaking changes.

## 🔧 Fixes

- Fix widget height not following its destiny sometimes
- Fix Splitter inner widget positioning

## 🔃 Refactors

- **Restructure widgets module**
- Change to Google docformat
- Rewrite `Container.get_lines` for brevity, efficiency and more features

## ➕ Additions

- **Add new mouse handling API**
  - Instead of relying on the glitchy `MouseTarget` API, widgets are now provided all `MouseActions` that occur over them. See the updated docs for [`Widget.handle_mouse`](https://ptg.bczsalba.com/pytermgui/widgets/base.html#Widget.handle_mouse).
- Add [`SizePolicy.RELATIVE`](https://ptg.bczsalba.com/pytermgui/enums#SizePolicy.RELATIVE) & [`Widget.relative_width`](https://ptg.bczsalba.com/pytermgui/widgets/base.html#Widget.relative_width)
- Add [`Overflow`](https://ptg.bczsalba.com/pytermgui/enums#Overflow) enum
- Add scrollable Container support using [`Overflow.SCROLL`](https://ptg.bczsalba.com/pytermgui/enums#Overflow.SCROLL)
- Add [callback binding](https://ptg.bczsalba.com/pytermgui/serializer.html#Serializer.bind) to `FileLoader` & `Serializer`
- Add [`VerticalAlignment`](https://ptg.bczsalba.com/pytermgui/enums.html#VerticalAlignment) enum & `Container` vertical alignment support
- Add [`WindowManager.focusing_actions`](https://ptg.bczsalba.com/pytermgui/window_manager.html#WindowManager.focusing_actions)
- Add support for vertically resizing Windows using the bottom border.

## ➖ Removals

- Remove redundant `_SYS_HAS_FRAME` in `ansi_interface`
