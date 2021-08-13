"""
pytermgui.cmd
-----------------
author: bczsalba


This module provides the command-line capabilities of the module.
"""

from __future__ import annotations

import sys
from random import randint
from itertools import zip_longest
from abc import ABC, abstractmethod
from typing import Any, Optional, Type
from argparse import ArgumentParser, Namespace

from . import (
    MarkupSyntaxError,
    prettify_markup,
    MarkupFormatter,
    WindowManager,
    real_length,
    define_tag,
    get_widget,
    InputField,
    Container,
    Splitter,
    Window,
    Button,
    Label,
    boxes,
    keys,
    ansi,
)

from .parser import NAMES as TOKENS


def _get_key_name(key: str) -> str:
    """Get canonical name of a key"""

    name = keys.get_name(key)
    if name is not None:
        return str("keys." + name)

    return ascii(key)


class Application(ABC):
    """A class to hold application details"""

    title: str
    description: str
    standalone: bool = False

    def __init__(self, manager: WindowManager) -> None:
        """Initialize object"""

        self.manager = manager

    @staticmethod
    def _update_widgets(window: Window, items: list[Any]) -> None:
        """Update window widgets, use auto() method on each item"""

        window.set_widgets([])
        for item in items:
            window += item

    @abstractmethod
    def finish(self, window: Window) -> None:
        """Print output information on Application finish.
        Called by the main method after self.manager exits.

        In order to support `standalone` mode, the Application should
        call `_request_exit()` once it is done with its duty. This method
        is called directly after."""

    @abstractmethod
    def construct_window(self) -> Window:
        """Construct an application window"""

    def _request_exit(self) -> None:
        """Send a request to parent manager to stop execution"""

        self.manager.stop()

    def _get_base_window(self, **attrs: Any) -> Window:
        """Get window with basic & universal settings applied"""

        if "title" not in attrs:
            attrs["title"] = " [bold wm-title]" + self.title + " "

        return Window(**attrs)


class LauncherApplication(Application):
    """Application class for launching other apps"""

    title = "Launcher"
    description = "Launch other apps"

    def __init__(self, manager: WindowManager, apps: list[Type[Application]]) -> None:
        """Initialize object"""

        super().__init__(manager)

        instantiated_apps: list[Application] = []
        for app in apps:
            instantiated_apps.append(app(manager))

        self.apps = instantiated_apps

    def finish(self, _: Window) -> None:
        """Do nothing on finish"""

    def construct_window(self) -> Window:
        """Construct an application window"""

        window = self._get_base_window(width=30) + ""
        manager = self.manager

        for app in self.apps:
            button = Button(
                app.title,
                lambda _, button: manager.add(button.app.construct_window()),
            )
            button.app = app
            window += button

        window += ""
        window += Label("[247 italic]> Choose an app to run", parent_align=0)

        return window


class GetchApplication(Application):
    """Application class for the getch() utility"""

    title = "Getch"
    description = "See your keypresses"

    def _key_callback(self, window: Window, key: str) -> None:
        """Edit window state if key is pressed"""

        name = _get_key_name(key)
        items = [
            "[wm-title]Your output",
            "",
            {"[wm-section]key": name},
            {"[wm-section]len()": str(len(key))},
            {"[wm-section]real_length()": str(real_length(key))},
        ]

        window.forced_width = 40
        self._update_widgets(window, items)

        if self.standalone:
            self._request_exit()
            return

        window.manager.print()

    def finish(self, window: Window) -> None:
        """Dump getch output"""

        for line in window.get_lines():
            print(line)

    def construct_window(self) -> Window:
        """Construct an application window"""

        window = self._get_base_window() + "[wm-title]Press any key..."
        window.bind(
            keys.ANY_KEY, self._key_callback, description="Read key & update window"
        )
        window.center()

        return window


class MarkupApplication(Application):
    """Application class for the markup parsing methods"""

    title = "MarkApp"
    description = "Play around with markup in this interactive editor."

    def __init__(self, manager: WindowManager) -> None:
        """Initialize object"""

        super().__init__(manager)

        self._255_color: str
        self._hex_color: str
        self._rgb_color: str

    @staticmethod
    def _get_tokens() -> list[Label]:
        """Get all tokens form the parser module"""

        tokens: list[str] = []
        for token in TOKENS:
            tokens.append(Label(f"[{token}]{token}", parent_align=0))

        return tokens

    @staticmethod
    def _get_colors() -> list[Label]:
        """Get all color tokens"""

        def _random_hex() -> str:
            """Return random hex number"""

            return "#%02X%02X%02X" % tuple(randint(0, 255) for _ in range(3))

        return [
            randint(0, 255),
            _random_hex(),
            _random_hex(),
        ]

    @staticmethod
    def _update_value(output: Label, field: InputField) -> None:
        """Update output value if field markup is valid"""

        try:
            ansi(field.value)
            output.value = field.value
        except MarkupSyntaxError as error:
            output.value = "[210 bold]SyntaxError:[/] " + error.escape_message()

    @staticmethod
    def _style_wrapper(_: int, item: str) -> str:
        """Avoid SyntaxError with `prettify_markup`"""

        try:
            # This method *always* returns str, but Mypy doesn't see that.
            return str(prettify_markup(item))

        except MarkupSyntaxError:
            return item

    def _update_colors(self, *_: Any) -> None:
        """Re-generate colors for guide"""

        self._255_color, self._hex_color, self._rgb_color = self._get_colors()

    def finish(self, window: Window) -> None:
        """Dump output markup"""

        window.manager.stop()
        print(prettify_markup(window.output_label.value))

    def construct_window(self) -> Window:
        """Construct an application window"""

        tokens = self._get_tokens()
        self._255_color, self._hex_color, self._rgb_color = self._get_colors()

        colors = [
            Label("[{color}]0-255", parent_align=2).set_style(
                "value", lambda _, item: ansi(item.format(color=self._255_color))
            ),
            Label("[{color}]#rrgggbb", parent_align=2).set_style(
                "value", lambda _, item: ansi(item.format(color=self._hex_color))
            ),
            Label("[{color}]rrr;ggg;bbb", parent_align=2).set_style(
                "value", lambda _, item: ansi(item.format(color=self._rgb_color))
            ),
        ]

        corners = Container.chars["corner"].copy()
        corners[0] += " [wm-title]tokens[/] "
        corners[1] = " [wm-title]colors[60] " + corners[1]

        guide = Container(forced_width=60).set_char("corner", corners)

        for token, color in zip_longest(tokens, colors, fillvalue=""):
            guide += {token: color}

        window = (
            self._get_base_window(resizable=True)
            + Container(
                Label(parent_align=0, id="output_label"),
                forced_width=60,
            )
            + guide
            + Label(
                "[247 italic]> Tip: Press CTRL_R to randomize colors", parent_align=0
            )
            + ""
            + InputField(id="input_field").set_style("fill", self._style_wrapper)
        )

        output = get_widget("output_label")
        field = get_widget("input_field")
        window.output_label = output

        field.bind(keys.ANY_KEY, lambda field, _: self._update_value(output, field))

        window.bind(
            keys.CTRL_R,
            self._update_colors,
            description="Randomize colors in the guide",
        )

        if self.standalone:
            field.bind(keys.RETURN, lambda *_: self._request_exit())

        window.center()
        return window


class HelperApplication(Application):
    """Application class to show all currently-active bindings"""

    title = "Help"
    description = "See all current bindings"

    def finish(self, window: Window) -> None:
        """Do nothing on finish"""

    def construct_window(self) -> Window:
        """Construct an application window"""

        window = self._get_base_window(width=50) + "[wm-title]Current bindings" + ""

        bindings = self.manager.list_bindings() + self.manager.focused.list_bindings()

        # Convert keycode into key name
        for i, binding in enumerate(bindings):
            binding_mutable = list(binding)
            binding_mutable[0] = _get_key_name(binding[0]).strip("'")
            bindings[i] = tuple(binding_mutable)

        # Sort keys according to key name length
        bindings.sort(key=lambda item: real_length(item[0]))

        for (key, _, description) in bindings:
            window += Label("[wm-section]" + key + ": ", parent_align=0)
            window += Label(description, padding=2, parent_align=0)
            window += ""

        window.bind(keys.ESC, lambda *_: window.close())

        return window.center()


def run_wm(args: Namespace) -> None:
    """Run WindowManager according to args"""

    # This is used for finding Application from arguments
    app_mapping = {
        "getch": GetchApplication,
        "markapp": MarkupApplication,
    }

    window: Optional[Window] = None

    with WindowManager() as manager:

        # Define styles
        define_tag("wm-title", "210")
        boxes.DOUBLE_TOP.set_chars_of(Window)
        boxes.SINGLE.set_chars_of(Container)

        style = MarkupFormatter("[60]{item}")
        for widget in [Window, Container]:
            widget.set_style("border", style)
            widget.set_style("corner", style)

        Splitter.set_style("separator", style)
        Splitter.set_char("separator", " " + boxes.SINGLE.borders[0])
        InputField.set_style("cursor", MarkupFormatter("[@72]{item}"))

        helper = HelperApplication(manager)

        # Setup bindings
        manager.bind(
            "*", lambda *_: manager.show_targets(), description="Show all mouse targets"
        )

        manager.bind(
            keys.CTRL_W,
            lambda *_: manager.focused.close(),
            description="Close focused window",
        )

        manager.bind(
            "?",
            lambda *_: manager.add(helper.construct_window()),
            description="Show all active bindings",
        )

        # Run with a launcher
        if len(sys.argv) == 1:
            launcher = LauncherApplication(manager, list(app_mapping.values()))
            manager.add(launcher.construct_window())

        # Run as standalone app
        if args.app:
            app = app_mapping[args.app.lower()](manager)
            app.standalone = True
            window = app.construct_window()
            manager.add(window)

        manager.run()

        # Run finish callback on standalone apps
        if window is not None:
            app.finish(window)


def main() -> None:
    """Main method"""

    parser = ArgumentParser(
        description="Command line interface & demo for some utilities related to TUI development."
    )
    parser.add_argument(
        "--app",
        type=str.lower,
        help="launch an app in standalone mode.",
        metavar="{Getch, MarkApp}",
        choices=["getch", "markapp"],
    )

    run_wm(parser.parse_args())


if __name__ == "__main__":
    main()
