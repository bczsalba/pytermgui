# Hey there!

Welcome to the **PyTermGUI** documentation!

For a general overview of the framework, follow the navigation at the bottom. For a set of working examples, check out the [walkthroughs](/walkthroughs) section. For a complete look at the API, see our [reference](/reference)!

![index image](/assets/screenshot.png)

## So what is a Terminal User Interface (or TUI) anyways?

A Terminal User Interface is, in general terms, a GUI in your terminal. Due to the terminal's attributes & limitations it can _only_ use plain text to display content, and has to arrange itself on the terminal's character grid.

In effect, this means terminal applications are:

- More constrained, which can often lead to more interesting solutions around known problems
- More standardized (though not enough)
- _Much_ faster to execute
- _Way cooler lookin'_

## If all that is true, why are TUIs so rare?

Historically, you had 2 options when writing a TUI:

- Create your own framework with its own rendering pipeline
- Use [curses](https://en.wikipedia.org/wiki/Curses_(programming_library)) or [ncurses](https://en.wikipedia.org/wiki/Ncurses)

Neither of these are simple to do; drawing in the terminal requires knowledge of a bunch of scattered standards and precedents, which, for the most part, are only available through _archaic_ documentation.

Things _have_ gotten a lot better in recent years. Projects like [Jexer](https://jexer.sourceforge.io/) and [notcurses](https://github.com/dankamongmen/notcurses) have shown how capable terminals are, and projects like [bubbletea](https://github.com/charmbracelet/bubbletea) and [tui-rs](https://github.com/fdehau/tui-rs) have made simplified and modernized TUI creation.

## How do we help the situation?

PTG provides abstractions for the low-level interactions with the terminal, and a modular widget system that is built ontop.

Our goals are the following:

- Versatility
- Expressive, readable but compact code
- No pointless abstractions
- Minimal dependencies

Because of the way the framework is built, you can implement the input-key-mouse-draw loop used internally by [WindowManager](/reference/pytermgui/window_manager.manager#pytermgui.window_manager.WindowManager) in {insert linecount} lines!

Widget layouts are explicit from the syntax of their creation. Widgets are rendered line-by-line, using the plain strings they return. There is built-in support for [keyboard](/widgets/custom#keyboard-input) & [mouse](/widgets/custom#mouse-input) inputs on all widgets, as well as the underlying low-level API that is used to make it all work.

This means that you, the user, can create TUI applications with workflows that rival the web in simplicity, without having to deal with the _massive_ fragmentation, framework war, and <sub>_shudders_</sub> CSS.
