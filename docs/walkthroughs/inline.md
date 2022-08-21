Our objective today will be to implement a function that lets us use PyTermGUI widgets in an inline-context, e.g. from the terminal prompt while retaining the shell's state.

This type of usage is common for simple prompts that are part of a greater, CLI-based application; they give you the cool-factor of the TUI, and in our case its mouse & keyboard input options, while staying in a CLI environment.

```termage-svg height=9 include=docs/src/inline_login.py
```

## Defining our goals

Our target syntax will be this:

```python
prompt_widget = ptg.inline(built_prompt())
```

...which gives us the general signature:

```python
def inline(widget):
    ...

    return widget
```

## Basic implementation

Let's start with getting the widget to read keyboard inputs and render after each one of them. To do this, we will sit in a `while` loop, use the [getch](/reference/pytermgui/input#pytermgui.input.getch) function and send its output to our widget's [handle_key](/reference/pytermgui/widgets/base#pytermgui.widgets.base.Widget.handle_key) method.

```python title="inline.py"
from pytermgui import getch, Widget

def inline(widget):
    while True:
        key = getch()

        widget.handle_key(key)

        for line in widget.get_lines():
            print(line)

    return widget
```

If you run the above, you will notice 2 things:

- Pressing ++ctrl+c++ leaves us with an ugly `KeyboardInterrupt`
- The widget lines aren't overwritten, but written to the terminal sequentially

There is also no mouse interaction, but we'll leave that for later.

## Implementing clean exits

Let's focus on our first problem, relating to the `KeyboardInterrupt` error. This is trivial to fix; we can tell `getch` to convert `KeyboardInterrupt` into the character ++ctrl+c++ sends, and break the loop when we see said character.

The reason we need to do this lies deep in the trenches of the terminal, but here is the gist: When ++ctrl+c++ is detected, the "interrupt" signal is sent to the current foreground task. This signal (in simple terms) tells the program:

> Hey there! I think you should stop running.

It's important to note that this is not a full hard _drop everything you're doing and flee_ signal. This one is meant to allow programs to clean up after themselves before quitting, which is exactly what we will need to do.

!!! note

    To see the above in effect, you can try the following code:

    ```python
    from time import time

    while True:
        try:
            print(time())
        except KeyboardInterrupt:
            pass

    return widget
    ```

    You will now be unable to leave the program, haha! Just kidding. Press ++ctrl+"\\"++ to send the "kill" signal to the program, which will stop the loop in its tracks. You can also press ++ctrl+l++, or type `reset` into the shell if your terminal got too messed up.

    I feel like this goes without saying, but:

    **Please do not put inescapable loops into your code**


=== "Changes"

    ```diff
      from typing import TypeVar
    - from pytermgui import getch, Widget
    + from pytermgui import getch, keys, Widget
      
      T = TypeVar("T", bound=Widget)
      
      def inline(widget):
          while True:
    -         key = getch()
    +         key = getch(interrupts=False)
    + 
    +         if key == keys.CTRL_C:
    +            break
      
              widget.handle_key(key)
     
              for line in widget.get_lines():
                 print(line)

          return widget
    ```

=== "Updated file"

    ```python linenums="1" title="inline.py"
    from typing import TypeVar
    from pytermgui import getch, keys, Widget
    
    T = TypeVar("T", bound=Widget)
    
    def inline(widget):
        while True:
            key = getch(interrupts=False)
    
            if key == keys.CTRL_C:
               break
    
            widget.handle_key(key)
    
            for line in widget.get_lines():
               print(line)

        return widget
    ```

If you now run this and press ++ctrl+c++, you should see the program quit cleanly.

## Improving printing

The print routine above was pretty rudimentary. We can do better!

To achieve the 'prompt' look we are aiming for, we need to always start printing at the same location. The simplest way to do this is to use the [save_cursor](/reference/pytermgui/ansi_interface#pytermgui.ansi_interface.save_cursor) and [restore_cursor](/reference/pytermgui/ansi_interface#pytermgui.ansi_interface.restore_cursor) methods. These tell the terminal to store the current cursor location somewhere, and to move the cursor to the stored location, respectively.

Let's start by making the following changes:


=== "Changes"

    ```diff
      from typing import TypeVar
    - from pytermgui import getch, keys, Widget
    + from pytermgui import getch, keys, save_cursor, restore_cursor, Widget
      
      def inline(widget):
          while True:
              key = getch(interrupts=False)
      
              if key == keys.CTRL_C:
                 break
      
              widget.handle_key(key) 

    +         save_cursor()
    +
              for line in widget.get_lines():
                 print(line)
    +
    +         restore_cursor()

          return widget
    ```

=== "Updated file"

    ```python linenums="1" title="inline.py"
    from typing import TypeVar
    from pytermgui import getch, keys, save_cursor, restore_cursor, Widget
     
    def inline(widget):
        while True:
            key = getch(interrupts=False)
    
            if key == keys.CTRL_C:
               break
    
            widget.handle_key(key) 

            save_cursor()
    
            for line in widget.get_lines():
               print(line)
    
            restore_cursor()

        return widget
    ```

This fixes the issue, but you may notice our widget only gets printed after the first input. That happens because we call `getch` before the first prints. Let's fix it, and also move the printing logic into an inner function to make things cleaner:

=== "Changes"

    ```diff
      from typing import TypeVar
      from pytermgui import getch, keys, save_cursor, restore_cursor, Widget

      def inline(widget):
    +     def _print_widget():
    +         save_cursor()
    +
    +         for line in widget.get_lines():
    +            print(line)
    +
    +         restore_cursor()
    +
    +     _print_widget()
    +
          while True:
              key = getch(interrupts=False)

              if key == keys.CTRL_C:
                 break

              widget.handle_key(key) 

    +         _print_widget()
    -         save_cursor()
    -
    -         for line in widget.get_lines():
    -            print(line)
    -
    -         restore_cursor()

          return widget
    ```

=== "Updated file"

    ```python linenums="1" title="inline.py"
    from typing import TypeVar
    from pytermgui import getch, keys, save_cursor, restore_cursor, Widget

    def inline(widget):
        def _print_widget():
            save_cursor()
    
            for line in widget.get_lines():
               print(line)
    
            restore_cursor()
    
        _print_widget()
    
        while True:
            key = getch(interrupts=False)

            if key == keys.CTRL_C:
               break

            widget.handle_key(key) 

            _print_widget()

        return widget
    ```

You may have noticed that when exiting, part of the widget remains on the screen. This is the _last_ print-related issue we need to fix!

We can use the [clear](/reference/pytermgui/ansi_interface#pytermgui.ansi_interface.clear) function with the "line" parameter to clear all the affected lines of the terminal.

Let's introduce a new inner function, `_clear_widget`:

```python linenums="15"
def _clear_widget():
    save_cursor()

    for _ in range(widget.height):
        clear("line")
        terminal.write("\n") # (1)

    restore_cursor()
    terminal.flush()
```

1. We need to increment the cursor using newlines to make sure we aren't just clearing the same line over and over.

To include this, we need to import both `clear` and `terminal`. We also probably want to call our new function, specifically **before** the call to print and at the end of our `inline` routine.

Here is a snapshot of our work so far:

=== "Changes"

    ```diff
      from typing import TypeVar
    - from pytermgui import getch, keys, save_cursor, restore_cursor, Widget
    + from pytermgui import (
    +     getch,
    +     keys,
    +     save_cursor,
    +     restore_cursor,
    +     Widget,
    +     clear,
    +     get_terminal,
    + )

      def inline(widget):
    +     # Make sure we use the global terminal
    +     terminal = get_terminal()
    +
          def _print_widget():
              save_cursor()
     
              for line in widget.get_lines():
                  print(line)
     
              restore_cursor()

    +     def _clear_widget():
    +         save_cursor()
    +
    +         for _ in range(widget.height):
    +             clear("line")
    +             terminal.write("\n")
    +
    +          restore_cursor()
    +          terminal.flush()
     
          _print_widget()
     
          while True:
              key = getch(interrupts=False)

              if key == keys.CTRL_C:
                  break

              widget.handle_key(key) 

    +         _clear_widget()
              _print_widget()
    +
    +     _clear_widget()
          return widget
    ```

=== "Updated file"

    ```python linenums="1" title="inline.py"
    from typing import TypeVar
    from pytermgui import (
        getch,
        keys,
        save_cursor,
        restore_cursor,
        Widget,
        clear,
        get_terminal,
    )

    def inline(widget):
        # Make sure we use the global terminal
        terminal = get_terminal()
    
        def _print_widget():
            save_cursor()
    
            for line in widget.get_lines():
                print(line)
    
            restore_cursor()

        def _clear_widget():
            save_cursor()
    
            for _ in range(widget.height):
                clear("line")
                terminal.write("\n")
    
            restore_cursor()
            terminal.flush()
    
        _print_widget()
    
        while True:
            key = getch(interrupts=False)

            if key == keys.CTRL_C:
                break

            widget.handle_key(key)

            _clear_widget()
            _print_widget()
    
        _clear_widget()
        return widget
    ```

And with that, our printing routine is exactly how we want it to be! Now onto the fancy things.

## Mouse support

Traditionally, mouse support is the "big bad" enemy of writing terminal programs. However, PyTermGUI makes it a _lot_ easier than you would've thought!

The only new thing we will need to import is the [mouse_handler](/reference/pytermgui/ansi_interface#pytermgui.ansi_interface.mouse_handler) context manager. This function does 2 things:

- Tells the terminal to send mouse events
- Returns a function that can translate mouse codes into [MouseEvent](/reference/pytermgui/ansi_interface#pytermgui.ansi_interface.MouseEvent) instances

To use it, we will wrap our `while True` loop into the context, and try to handle keys as mouse events when our widget didn't handle them successfully. Each widget denotes "successful" event handling by returning `True` from the given method, so the check will be simple:

```diff linenums="37"
+ with mouse_handler(["press_hold", "hover"], "decimal_xterm") as translate:
      while True:
          key = getch(interrupts=False)

          if key == keys.CTRL_C:
              break

-         widget.handle_key(key)
+         if not widget.handle_key(key):
+             for event in translate(key):
+                 if event is None:
+                     continue
+                 widget.handle_mouse(event)

          _clear_widget()
          _print_widget()

_clear_widget()
return widget
```

There is a tiny bug with our mouse handling, however. We never tell the widget _where_ it is located, so it will reject most events. We can easily fix this by using the [report_mouse](/reference/pytermgui/ansi_interface#pytermgui.ansi_interface.report_mouse) and inserting the following line at the top of our function:

```python
widget.pos = report_cursor()
```


With the above changes, our file looks like the following:

```python linenums="1" title="inline.py"
from typing import TypeVar
from pytermgui import (
    getch,
    keys,
    save_cursor,
    restore_cursor,
    report_cursor,
    Widget,
    clear,
    get_terminal,
    mouse_handler,
)

def inline(widget):
    # Make sure we use the global terminal
    terminal = get_terminal()

    widget.pos = report_cursor()

    def _print_widget():
        save_cursor()

        for line in widget.get_lines():
            print(line)

        restore_cursor()

    def _clear_widget():
        save_cursor()

        for _ in range(widget.height):
            clear("line")
            terminal.write("\n")

        restore_cursor()
        terminal.flush()

    _print_widget()

    with mouse_handler(["press_hold", "hover"], "decimal_xterm") as translate:
        while True:
            key = getch(interrupts=False)

            if key == keys.CTRL_C:
                break

            if not widget.handle_key(key):
                events = translate(key)
                # Don't try iterating when there are no events
                if events is None:
                    continue

                for event in events:
                    if event is None:
                        continue
                    widget.handle_mouse(event)

            _clear_widget()
            _print_widget()

    _clear_widget()
    return widget
```

## Congratulations!

**You just implemented PyTermGUI's [inline](/reference/pytermgui/widgets/inline#pytermgui.widgets.inline) function!**

Make sure to look at its source code for the final version of the code we've been working with, along with a few extra improvements, such as handling each the widget's `positioned_line_buffer`.
