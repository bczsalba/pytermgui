While the default widgets are pretty nifty themselves, sometimes you might wanna do your own thing. Luckily for you, PyTermGUI's `Widget` API is ridiculously easy to build upon!

## What to know

Firstly, you should know some things about the shape and function of various parts of the API.

### Output & rendering

The most important method to a widget is its `get_lines`. This returns a list of strings, which is what is used to eventually display it in the terminal. This method is called a _healthy_ amount, so you probably wanna make all state changes in some other place, so `get_lines` can request _mostly_ static data.

### Selectables

Each widget can be made selectable by either setting `widget._selectables_length` to a non-zero value, or overwriting the `selectables_length` property of said widget.

If you want to make parent widgets know that your widget can be selected, you can just define `_selectables_length` as 1. If you have multiple inner-widgets you need to handle selecting, you should inherit from `Container` and let it handle all the plumbing for you. If you're interested in how it does all that magic, see it's [selectables](/reference/pytermgui/widgets/containers#pytermgui.widgets.containers.Container.selectables) property, and its [select](/reference/pytermgui/widgets/containers#pytermgui.widgets.containers.Container.select) method.

### Input handling

Both keyboard and mouse inputs are cascaded down from the `WindowManager` to each widget. A widget can mark some input as "handled" and stop it from cascading further by having its handler method return `True`.

!!! note

    The base `Widget` class may go through some routines for each input, such as calling any widget bindings, or, in the case of mouse inputs, call semantic handlers.

    Because of this, and to ensure future backwards-compatibility (weird phrase, I know), you should start all your input handlers by calling the parent class' handler:

    ```python
    class MyWidget(Widget):
        def handle_key(self, key: str) -> bool:
            if super().handle_key(key):
                return

            # Do our own handling
    ```


#### Keyboard input

The signature of the keyboard handler is pretty simple:

```python
def handle_key(self, key: str) -> bool
```

To compare key codes to canonical names (e.g. `CTRL_B` to `\x02`), you can use the `keys` singleton:

```python
from pytermgui import Widget, keys


class MyWidget(Widget):
    def handle_key(self, key: str) -> bool:
        if super().handle_key(key):
            return True

        if key == keys.CTRL_F:
            self.do_something()
            return True

        return False
```

#### Mouse input

While terminal mouse inputs are historically pretty hard to handle, PTG offers a simple interface to hide all that paperwork. 

An interface symmetrical to the keyboard handlers exists, and is the base of all that comes below:

```python
def handle_mouse(self, event: MouseEvent) -> bool:
```

The only argument is the `event`, which is an instance of [MouseEvent](/reference/pytermgui/ansi_interface/#pytermgui.ansi_interface.MouseEvent). This is what it looks like:

```termage-svg height=28 title=inspect(MouseEvent)
from pytermgui import MouseEvent, inspect

print(inspect(MouseEvent))
```

Depending on your circumstances, you can test the event's `position` or `action` attributes:

```python
from pytermgui import Widget, MouseEvent, MouseAction

class MyWidget(Widget):
    def handle_mouse(self, event: MouseEvent) -> bool:
        if super().handle_mouse(event):
            return True

        if event.action == MouseAction.LEFT_CLICK:
            self.do_something()
```

Since comparing against actions gets a _li'l_ tedious over time, we have a system called **semantic mouse handlers** to help you. These are optional methods that are looked for when `Widget` is handling some mouse event, and only called when present.

They all follow the syntax `on_{event_name}`. events can be one of:

```python
[
    "left_click",
    "right_click",
    "click",
    "left_drag",
    "right_drag",
    "drag",
    "scroll_up",
    "scroll_down",
    "scroll",
    "shift_scroll_up",
    "shift_scroll_down",
    "shift_scroll",
    "hover",
]
```

Handler methods are looked for in the order of highest specifity. For example, the following widget:

```python
from pytermgui import MouseEvent, Widget


class MyWidget(Widget):
    label: str = "No action"

    def get_lines(self) -> list[str]:
        return [self.label]

    def on_left_click(self, event: MouseEvent) -> bool:
        self.label = "Left click"

        return True

    def on_click(self, event: MouseEvent) -> bool:
        self.label = "Generic click"

        return True 

    def handle_mouse(self, event: MouseEvent) -> bool:
        # Make sure we call the super handler
        if super().handle_mouse(event):
            return True

        self.label = "No action"
        return True
```

...will display `Left click` only on left clicks, `Generic click` only on right clicks (as `on_right_click` isn't defined) and `No action` on any other mouse input.


## FAQ

### How do I dynamically update a widget's content?

The pattern I've come to adopt for this purpose is based on a regularly updated inner state that gets displayed within `get_lines`. For example, let's say we have a `Weather` widget that regularly requests weather information and displays it. 

Here is how I would do it. Take _extra_ notice of the highlighted lines:

```termage include=docs/src/widgets/weather.py linenums="1" hl_lines="51 52 62 63 64 65 66 67 68 69"
```

As you can see, I made the widget inherit `Container`. This is _usually_ what you want when dealing with a widget that:

- Contains inner content representable by sub-widgets (`Label` in our case)
- Has to periodically update said inner content

We also use a thread to do all the monitoring & updating, instead of doing it in `get_lines` or some other periodically called method. Since `get_lines` is called _very_ regularly, and its time-to-return is critical for the rendering of an application, we need to make sure to avoid putting anything with noticable delays in there.

??? warning "Don't overuse threads"
    
    If you have multiple widgets that run on a thread-based monitor, you are likely better of creating a single master thread that updates every widget periodically. A simple monitor implementation like the following should work alright:

    ```python
    from __future__ import annotations

    from dataclasses import dataclass, field
    from threading import Thread
    from time import sleep, time
    from typing import Callable


    @dataclass
    class Listener:
        callback: Callable[[], None]
        period: float
        time_till_next: float


    @dataclass
    class Monitor:
        update_frequency: float = 0.5
        listeners: list[Listener] = field(default_factory=list)

        def attach(self, callback: Callable[[], None], *, period: float) -> Listener:
            listener = Listener(callback, period, period)
            self.listeners.append(listener)

            return listener

        def start(self) -> Monitor:
            def _monitor() -> None:
                previous = time()

                while True:
                    elapsed = time() - previous

                    for listener in self.listeners:
                        listener.time_till_next -= elapsed

                        if listener.time_till_next <= 0.0:
                            listener.callback()
                            listener.time_till_next = listener.period

                    previous = time()
                    sleep(self.update_frequency)

            Thread(target=_monitor).start()
            return self
    ```

    You can then use this in your widgets:

    ```py
    from .monitor import Monitor
    from pytermgui import Container

    monitor = Monitor().start()

    class Weather(Container):
        def __init__(self, location: str, timeout: float, **attrs: Any) -> None:
            ...  # Standard init code (see above)

            monitor.attach(self._request_and_update, timeout) 

        def _request_and_update(self) -> None:
            self.data = self._request()
            self.update_content()
    ```

**Let's talk about those highlighted lines, shall we?**

In the first set of lines we send out a request to the (imaginary) external API, and update ourselves accordingly. This update is done in the second set of lines, where the `set_widgets` method is used to overwrite the current widget selection.

**Why use this method instead of manually overwriting `_widgets`?**

The reason this method was created in the first place was to simplify the process of:

- Emptying the container's widgets
- Resetting its height
- Going through a list, running `auto` on each item and adding it to the container

It makes things a lot simpler, and it also accounts for any future oddities that mess with the process!

### How do I periodically refresh live data?

The window manager's compositor calls `get_lines` regularly and redraws changed output,
so you do not need to invalidate the window or call a refresh method. Keep slow work,
such as an API or database request, on a worker thread and let the widget apply the
result during rendering:

```python
from __future__ import annotations

from threading import Event, Lock, Thread
from time import strftime

import pytermgui as ptg


class LiveTable(ptg.Container):
    """A table whose next set of rows can be prepared by another thread."""

    def __init__(self, **attrs) -> None:
        self._pending_lock = Lock()
        self._pending: list[str] | None = None
        super().__init__(box="SINGLE", **attrs)

    def update_rows(self, rows: list[tuple[str, str, str]]) -> None:
        widgets = ["[bold]Job | State   | Updated[/]"]
        widgets.extend(
            f"{job:<3} | {state:<7} | {updated}" for job, state, updated in rows
        )

        # Only exchange prepared data here. set_widgets is called from get_lines,
        # rather than while the compositor may be iterating over the old widgets.
        with self._pending_lock:
            self._pending = widgets

    def get_lines(self) -> list[str]:
        with self._pending_lock:
            pending = self._pending
            self._pending = None

        if pending is not None:
            self.set_widgets(pending)

        return super().get_lines()


def request_jobs() -> list[tuple[str, str, str]]:
    """Replace this body with your API or database request."""

    now = strftime("%H:%M:%S")
    return [("A", "running", now), ("B", "queued", now)]


def monitor(table: LiveTable, stop: Event, period: float) -> None:
    while not stop.is_set():
        table.update_rows(request_jobs())
        stop.wait(period)


manager = ptg.WindowManager()
table = LiveTable(static_width=36)
manager.add(ptg.Window(table, box="EMPTY"))

stop = Event()
Thread(target=monitor, args=(table, stop, 2.0), daemon=True).start()

try:
    manager.run()
finally:
    stop.set()
```

`Event.wait` provides both the interval and a way to stop the worker when the manager
exits. The worker only publishes completed rows under a lock; it does not mutate the
container's private `_widgets` list. `set_widgets` performs the conversion to child
widgets and sets their parent and dimensions correctly.
