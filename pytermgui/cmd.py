"""The command-line module of the library.

See ptg --help for more information.
"""

from __future__ import annotations

import os
import sys
import random
import builtins
import importlib
from platform import platform
from itertools import zip_longest
from argparse import ArgumentParser, Namespace
from typing import Any, Callable, Iterable, Type

import pytermgui as ptg


def _title() -> str:
    """Returns 'PyTermGUI', formatted."""

    return "[!gradient(210) bold]PyTermGUI[/!gradient /]"


class AppWindow(ptg.Window):
    """A generic application window.

    It contains a header with the app's title, as well as some global
    settings.
    """

    app_title: str
    """The display title of the application."""

    app_id: str
    """The short identifier used by ArgumentParser."""

    standalone: bool
    """Whether this app was launched directly from the CLI."""

    overflow = ptg.Overflow.SCROLL
    vertical_align = ptg.VerticalAlignment.TOP

    def __init__(self, args: Namespace | None = None, **attrs: Any) -> None:
        super().__init__(**attrs)

        self.standalone = bool(getattr(args, self.app_id, None))

        bottom = ptg.Container.chars["border"][-1]
        header_box = ptg.boxes.Box(
            [
                "",
                " x ",
                bottom * 3,
            ]
        )

        self._add_widget(ptg.Container(f"[ptg.title]{self.app_title}", box=header_box))
        self._add_widget("")

    def setup(self) -> None:
        """Centers window, sets its width & height."""

        self.width = int(self.terminal.width * 2 / 3)
        self.height = int(self.terminal.height * 2 / 3)
        self.center(store=False)

    def on_exit(self) -> None:
        """Called on application exit.

        Should be used to print current application state to the user's shell.
        """

        ptg.tim.print(f"{_title()} - [dim]{self.app_title}")
        print()


class GetchWindow(AppWindow):
    """A window for the Getch utility."""

    app_title = "Getch"
    app_id = "getch"

    def __init__(self, args: Namespace | None = None, **attrs: Any) -> None:
        super().__init__(args, **attrs)

        self.bind(ptg.keys.ANY_KEY, self._update)

        self._content = ptg.Container("Press any key...", static_width=50)
        self._add_widget(self._content)

        self.setup()

    def _update(self, _: ptg.Widget, key: str) -> None:
        """Updates window contents on keypress."""

        self._content.set_widgets([])
        name = _get_key_name(key)

        if name != ascii(key):
            name = f"keys.{name}"

        style = ptg.HighlighterStyle(ptg.highlight_python)

        items = [
            "[ptg.title]Your output",
            "",
            {"[ptg.detail]key": ptg.Label(name, style=style)},
            {"[ptg.detail]value:": ptg.Label(ascii(key), style=style)},
            {"[ptg.detail]len()": ptg.Label(str(len(key)), style=style)},
            {
                "[ptg.detail]real_length()": ptg.Label(
                    str(ptg.real_length(key)), style=style
                )
            },
        ]

        for item in items:
            self._content += item

        if self.standalone:
            assert self.manager is not None
            self.manager.stop()

    def on_exit(self) -> None:
        super().on_exit()

        for line in self._content.get_lines():
            print(line)


class ColorPickerWindow(AppWindow):
    """A window to pick colors from the xterm-256 palette."""

    app_title = "ColorPicker"
    app_id = "color"

    def __init__(self, args: Namespace | None = None, **attrs: Any) -> None:
        super().__init__(args, **attrs)

        self._chosen_rgb = ptg.str_to_color("black")

        self._colorpicker = ptg.ColorPicker()
        self._add_widget(ptg.Collapsible("xterm-256", "", self._colorpicker).expand())
        self._add_widget("")
        self._add_widget(
            ptg.Collapsible(
                "RGB & HEX", "", self._create_rgb_picker(), static_width=81
            ).expand(),
        )

        self.setup()

    def _create_rgb_picker(self) -> ptg.Container:
        """Creates the RGB picker 'widget'."""

        root = ptg.Container(static_width=72)

        matrix = ptg.DensePixelMatrix(68, 20)
        hexdisplay = ptg.Label()
        rgbdisplay = ptg.Label()

        sliders = [ptg.Slider() for _ in range(3)]

        def _get_rgb() -> tuple[int, int, int]:
            """Computes the RGB value from the 3 sliders."""

            values = [int(255 * slider.value) for slider in sliders]

            return values[0], values[1], values[2]

        def _update(*_) -> None:
            """Updates the matrix & displays with the current color."""

            color = self._chosen_rgb = ptg.RGBColor.from_rgb(_get_rgb())
            for row in range(matrix.rows):
                for col in range(matrix.columns):
                    matrix[row, col] = color.hex

            hexdisplay.value = f"[ptg.body]{color.hex}"
            rgbdisplay.value = f"[ptg.body]rgb({', '.join(map(str, color.rgb))})"
            matrix.build()

        red, green, blue = sliders

        # red.styles.filled_selected__cursor = "red"
        # green.styles.filled_selected__cursor = "green"
        # blue.styles.filled_selected__cursor = "blue"

        for slider in sliders:
            slider.onchange = _update

        root += hexdisplay
        root += rgbdisplay
        root += ""

        root += matrix
        root += ""

        root += red
        root += green
        root += blue

        _update()
        return root

    def on_exit(self) -> None:
        super().on_exit()

        color = self._chosen_rgb
        eightbit = " ".join(
            button.get_lines()[0] for button in self._colorpicker.chosen
        )

        ptg.tim.print("[ptg.title]Your colors:")
        ptg.tim.print(f"    [{color.hex}]{color.rgb}[/] // [{color.hex}]{color.hex}")
        ptg.tim.print()
        ptg.tim.print(f"    {eightbit}")


class TIMWindow(AppWindow):
    """An application to play around with TIM."""

    app_title = "TIM Playground"
    app_id = "tim"

    def __init__(self, args: Namespace | None = None, **attrs: Any) -> None:
        super().__init__(args, **attrs)

        if self.standalone:
            self.bind(
                ptg.keys.RETURN,
                lambda *_: self.manager.stop() if self.manager is not None else None,
            )

        self._generate_colors()

        self._output = ptg.Label(parent_align=0)

        self._input = ptg.InputField()
        self._input.styles.value__fill = lambda _, item: item

        self._showcase = self._create_showcase()

        self._input.bind(ptg.keys.ANY_KEY, lambda *_: self._update_output())

        self._add_widget(
            ptg.Container(
                ptg.Container(self._output),
                self._showcase,
                ptg.Container(self._input),
                box="EMPTY",
                static_width=60,
            )
        )

        self.bind(ptg.keys.CTRL_R, self._generate_colors)

        self.setup()

        self.select(0)

    @staticmethod
    def _random_rgb() -> ptg.Color:
        """Returns a random Color."""

        rgb = tuple(random.randint(0, 255) for _ in range(3))

        return ptg.RGBColor.from_rgb(rgb)  # type: ignore

    def _update_output(self) -> None:
        """Updates the output field."""

        self._output.value = self._input.value

    def _generate_colors(self, *_) -> None:
        """Generates self._example_{255,rgb,hex}."""

        ptg.tim.alias("ptg.timwindow.255", str(random.randint(16, 233)))
        ptg.tim.alias("ptg.timwindow.rgb", ";".join(map(str, self._random_rgb().rgb)))
        ptg.tim.alias("ptg.timwindow.hex", self._random_rgb().hex)

    @staticmethod
    def _create_showcase() -> ptg.Container:
        """Creates the showcase container."""

        def _show_style(name: str) -> str:
            return f"[{name}]{name}"

        def _create_table(source: Iterable[tuple[str, str]]) -> ptg.Container:
            root = ptg.Container()

            for left, right in source:
                row = ptg.Splitter(
                    ptg.Label(left, parent_align=0), ptg.Label(right, parent_align=2)
                ).styles(separator="ptg.border")

                row.set_char("separator", f" {ptg.Container.chars['border'][0]}")

                root += row

            return root

        prefix = "ptg.timwindow"
        tags = [_show_style(style) for style in ptg.tim.tags]
        colors = [
            f"[[{prefix}.255]0-255[/]]",
            f"[[{prefix}.hex]#RRGGBB[/]]",
            f"[[{prefix}.rgb]RRR;GGG;BBB[/]]",
            "",
            f"[[inverse {prefix}.255]@0-255[/]]",
            f"[[inverse {prefix}.hex]@#RRGGBB[/]]",
            f"[[inverse {prefix}.rgb]@RRR;GGG;BBB[/]]",
        ]

        tag_container = _create_table(zip_longest(tags, colors, fillvalue=""))
        user_container = _create_table(
            (_show_style(tag), f"[!expand {tag}]{tag}") for tag in ptg.tim.user_tags
        )

        return ptg.Container(tag_container, user_container, box="EMPTY")

    def on_exit(self) -> None:
        super().on_exit()
        print(ptg.tim.prettify_markup(self._input.value))
        ptg.tim.print(self._input.value)


class InspectorWindow(AppWindow):
    """A window for the `inspect` utility."""

    app_title = "Inspector"
    app_id = "inspect"

    def __init__(self, args: Namespace | None = None, **attrs: Any) -> None:
        super().__init__(args, **attrs)

        self._input = ptg.InputField(value="boxes.Box")

        self._output = ptg.Container(box="EMPTY")
        self._update()

        self._input.bind(ptg.keys.ENTER, self._update)

        self._add_widget(
            ptg.Container(
                self._output,
                "",
                ptg.Container(self._input),
                box="EMPTY",
            )
        )

        self.setup()

        self.select(0)

    @staticmethod
    def obj_from_path(path: str) -> object | None:
        """Retrieves an object from any valid import path.

        An import path could be something like:
            pytermgui.window_manager.compositor.Compositor

        ...or if the library in question imports its parts within `__init__.py`-s:
            pytermgui.Compositor
        """

        parts = path.split(".")

        if parts[0] in dir(builtins):
            obj = getattr(builtins, parts[0])

        elif parts[0] in dir(ptg):
            obj = getattr(ptg, parts[0])

        else:
            try:
                obj = importlib.import_module(".".join(parts[:-1]))
            except (ValueError, ModuleNotFoundError) as error:
                return (
                    f"Could not import object at path {path!r}: {error}."
                    + " Maybe try using the --eval flag?"
                )

        try:
            obj = getattr(obj, parts[-1])
        except AttributeError:
            return obj

        return obj

    def _update(self, *_) -> None:
        """Updates output with new inspection result."""

        obj = self.obj_from_path(self._input.value)

        self._output.vertical_align = ptg.VerticalAlignment.CENTER
        self._output.set_widgets([ptg.inspect(obj)])

    def on_exit(self) -> None:
        super().on_exit()

        self._output.vertical_align = ptg.VerticalAlignment.TOP
        for line in self._output.get_lines():
            print(line)


APPLICATION_MAP = {
    ("Getch", "getch"): GetchWindow,
    ("Inspector", "inspect"): InspectorWindow,
    ("ColorPicker", "color"): ColorPickerWindow,
    ("TIM Playground", "tim"): TIMWindow,
}


def _app_from_short(short: str) -> Type[AppWindow]:
    """Finds an AppWindow constructor from its short name."""

    for (_, name), app in APPLICATION_MAP.items():
        if name == short:
            return app

    raise KeyError(f"No app found for {short!r}")


def process_args(argv: list[str] | None = None) -> Namespace:
    """Processes command line arguments."""

    parser = ArgumentParser(
        description=f"{ptg.tim.parse(_title())}'s command line environment."
    )

    apps = [short for (_, short), _ in APPLICATION_MAP.items()]

    app_group = parser.add_argument_group("Applications")
    app_group.add_argument(
        "--app",
        type=str.lower,
        help="Launch an app.",
        metavar=f"{', '.join(app.capitalize() for app in apps)}",
        choices=apps,
    )

    app_group.add_argument(
        "-g", "--getch", help="Launch the Getch app.", action="store_true"
    )

    app_group.add_argument(
        "-t", "--tim", help="Launch the TIM Playground app.", action="store_true"
    )

    app_group.add_argument(
        "-c",
        "--color",
        help="Launch the ColorPicker app.",
        action="store_true",
    )

    inspect_group = parser.add_argument_group("Inspection")
    inspect_group.add_argument(
        "-i", "--inspect", help="Inspect an object.", metavar="PATH_OR_CODE"
    )
    inspect_group.add_argument(
        "-e",
        "--eval",
        help="Evaluate the expression given to `--inspect` instead of treating it as a path.",
        action="store_true",
    )

    inspect_group.add_argument(
        "--methods", help="Always show methods when inspecting.", action="store_true"
    )
    inspect_group.add_argument(
        "--dunder",
        help="Always show __dunder__ methods when inspecting.",
        action="store_true",
    )
    inspect_group.add_argument(
        "--private",
        help="Always show _private methods when inspecting.",
        action="store_true",
    )

    util_group = parser.add_argument_group("Utilities")
    util_group.add_argument(
        "-s",
        "--size",
        help="Output the current terminal size in WxH format.",
        action="store_true",
    )

    util_group.add_argument(
        "-v",
        "--version",
        help="Print version & system information.",
        action="store_true",
    )

    util_group.add_argument(
        "--highlight",
        help=(
            "Highlight some python-like code syntax."
            + " No argument or '-' will read STDIN."
        ),
        metavar="SYNTAX",
        const="-",
        nargs="?",
    )

    util_group.add_argument(
        "--exec",
        help="Execute some Python code. No argument or '-' will read STDIN.",
        const="-",
        nargs="?",
    )

    util_group.add_argument("-f", "--file", help="Interpret a PTG-YAML file.")
    util_group.add_argument(
        "--print-only",
        help="When interpreting YAML, print the environment without running it interactively.",
        action="store_true",
    )

    export_group = parser.add_argument_group("Exporters")

    export_group.add_argument(
        "--export-svg",
        help="Export the result of any non-interactive argument as an SVG file.",
        metavar="FILE",
    )
    export_group.add_argument(
        "--export-html",
        help="Export the result of any non-interactive argument as an HTML file.",
        metavar="FILE",
    )

    argv = argv or sys.argv[1:]
    args = parser.parse_args(args=argv)

    return args


def screenshot(man: ptg.WindowManager) -> None:
    """Opens a modal dialogue & saves a screenshot."""

    tempname = ".screenshot_temp.svg"

    modal: ptg.Window

    def _finish(*_: Any) -> None:
        """Closes the modal and renames the window."""

        man.remove(modal)
        filename = field.value or "screenshot"

        if not filename.endswith(".svg"):
            filename += ".svg"

        os.rename(tempname, filename)

        man.toast("[ptg.title]Screenshot saved!", "", f"[ptg.detail]{filename}")

    title = sys.argv[0]
    field = ptg.InputField(prompt="Save as: ")

    man.screenshot(title=title, filename=tempname)

    modal = man.alert(
        "[ptg.title]Screenshot taken!", "", ptg.Container(field), "", ["Save!", _finish]
    )


def _get_key_name(key: str) -> str:
    """Gets canonical name of a key.

    Arguments:
        key: The key in question.

    Returns:
        The canonical-ish name of the key.
    """

    name = ptg.keys.get_name(key)
    if name is not None:
        return name

    return ascii(key)


def _create_header() -> ptg.Window:
    """Creates an application header window."""

    content = ptg.Splitter(ptg.Label("PyTermGUI", parent_align=0, padding=2))
    content.styles.fill = "ptg.header"

    return ptg.Window(content, box="EMPTY", id="ptg.header", is_persistent=True)


def _create_app_picker(manager: ptg.WindowManager) -> ptg.Window:
    """Creates a dropdown that allows picking between applications."""

    existing_windows: list[ptg.Window] = []

    def _wrap(func: Callable[[ptg.Widget], Any]) -> Callable[[ptg.Widget], Any]:
        def _inner(caller: ptg.Widget) -> None:
            dropdown.collapse()

            window: ptg.Window = func(caller)
            if type(window) in map(type, manager):
                return

            existing_windows.append(window)
            manager.add(window, assign="body")

            body = manager.layout.body

            body.content = window
            manager.layout.apply()

        return _inner

    buttons = [
        ptg.Button(label, _wrap(lambda *_, app=app: app()))
        for (label, _), app in APPLICATION_MAP.items()
    ]

    dropdown = ptg.Collapsible("Applications", *buttons, keyboard=True).styles(
        fill="ptg.footer"
    )

    return ptg.Window(
        dropdown,
        box="EMPTY",
        id="ptg.header",
        is_persistent=True,
        overflow=ptg.Overflow.RESIZE,
    ).styles(fill="ptg.header")


def _create_footer(man: ptg.WindowManager) -> ptg.Window:
    """Creates a footer based on the manager's bindings."""

    content = ptg.Splitter().styles(fill="ptg.footer")
    for key, (callback, doc) in man.bindings.items():
        if doc == f"Binding of {key} to {callback}":
            continue

        content.lazy_add(
            ptg.Button(
                f"{_get_key_name(str(key))} - {doc}",
                onclick=lambda *_, _callback=callback: _callback(man),
            )
        )

    return ptg.Window(content, box="EMPTY", id="ptg.footer", is_persistent=True)


def _create_layout() -> ptg.Layout:
    """Creates the main layout."""

    layout = ptg.Layout()

    layout.add_slot("Header", height=1)
    layout.add_slot("Applications", width=20)
    layout.add_break()
    layout.add_slot("Body")
    layout.add_break()
    layout.add_slot("Footer", height=1)

    return layout


def _create_aliases() -> None:
    """Creates all TIM alises used by the `ptg` utility.

    Current aliases:
    - ptg.title: Used for main titles.
    - ptg.body: Used for body text.
    - ptg.detail: Used for highlighting detail inside body text.
    - ptg.accent: Used as an accent color in various places.
    - ptg.header: Used for the header bar.
    - ptg.footer: Used for the footer bar.
    - ptg.border: Used for focused window borders & corners.
    - ptg.border_blurred: Used for non-focused window borders & corners.
    """

    ptg.tim.alias("ptg.title", "210 bold")
    ptg.tim.alias("ptg.body", "247")
    ptg.tim.alias("ptg.detail", "dim")
    ptg.tim.alias("ptg.accent", "72")

    ptg.tim.alias("ptg.header", "@235 242 bold")
    ptg.tim.alias("ptg.footer", "@235")

    ptg.tim.alias("ptg.border", "60")
    ptg.tim.alias("ptg.border_blurred", "#373748")


def _configure_widgets() -> None:
    """Configures default widget attributes."""

    ptg.boxes.Box([" ", " x ", " "]).set_chars_of(ptg.Window)
    ptg.boxes.SINGLE.set_chars_of(ptg.Container)
    ptg.boxes.DOUBLE.set_chars_of(ptg.Window)

    ptg.InputField.styles.cursor = "inverse ptg.accent"
    ptg.InputField.styles.fill = "245"
    ptg.Container.styles.border__corner = "ptg.border"
    ptg.Splitter.set_char("separator", "")
    ptg.Button.set_char("delimiter", ["  ", "  "])

    ptg.Window.styles.border__corner = "ptg.border"
    ptg.Window.set_focus_styles(
        focused=("ptg.border", "ptg.border"),
        blurred=("ptg.border_blurred", "ptg.border_blurred"),
    )


def run_environment(args: Namespace) -> None:
    """Runs the WindowManager environment.

    Args:
        args: An argparse namespace containing relevant arguments.
    """

    def _find_focused(manager: ptg.WindowManager) -> ptg.Window | None:
        if manager.focused is None:
            return None

        # Find foremost non-persistent window
        for window in manager:
            if window.is_persistent:
                continue

            return window

        return None

    def _toggle_attachment(manager: ptg.WindowManager) -> None:
        focused = _find_focused(manager)

        if focused is None:
            return

        slot = manager.layout.body
        if slot.content is None:
            slot.content = focused
        else:
            slot.detach_content()

        manager.layout.apply()

    def _close_focused(manager: ptg.WindowManager) -> None:
        focused = _find_focused(manager)

        if focused is None:
            return

        focused.close()

    _configure_widgets()

    window: AppWindow | None = None
    with ptg.WindowManager() as manager:
        app_picker = _create_app_picker(manager)

        manager.bind(
            ptg.keys.CTRL_W,
            lambda *_: _close_focused(manager),
            "Close window",
        )
        manager.bind(
            ptg.keys.F12,
            lambda *_: screenshot(manager),
            "Screenshot",
        )
        manager.bind(
            ptg.keys.CTRL_F,
            lambda *_: _toggle_attachment(manager),
            "Toggle layout",
        )

        manager.bind(
            ptg.keys.CTRL_A,
            lambda *_: {
                manager.focus(app_picker),  # type: ignore
                app_picker.execute_binding(ptg.keys.CTRL_A),
            },
        )
        manager.bind(
            ptg.keys.ALT + ptg.keys.TAB,
            lambda *_: manager.focus_next(),
        )

        if not args.app:
            manager.layout = _create_layout()

            manager.add(_create_header(), assign="header")
            manager.add(app_picker, assign="applications")
            manager.add(_create_footer(manager), assign="footer")

            manager.toast(
                f"[ptg.title]Welcome to the {_title()} [ptg.title]CLI!",
                offset=ptg.terminal.height // 2 - 3,
                delay=700,
            )

        else:
            manager.layout.add_slot("Body")

            app = _app_from_short(args.app)
            window = app(args)
            manager.add(window, assign="body")

    window = window or manager.focused  # type: ignore
    if window is None or not isinstance(window, AppWindow):
        return

    window.on_exit()


def _print_version() -> None:
    """Prints version info."""

    def _print_aligned(left: str, right: str | None) -> None:
        left += ":"

        ptg.tim.print(f"[ptg.detail]{left:<19} [/ptg.detail 157]{right}")

    ptg.tim.print(
        f"[bold !gradient(210)]PyTermGUI[/ /!gradient] version [157]{ptg.__version__}"
    )
    ptg.tim.print()
    ptg.tim.print("[ptg.title]System details:")

    _print_aligned("    Python version", sys.version.split()[0])
    _print_aligned("    $TERM", os.getenv("TERM"))
    _print_aligned("    $COLORTERM", os.getenv("COLORTERM"))
    _print_aligned("    Color support", str(ptg.terminal.colorsystem))
    _print_aligned("    OS Platform", platform())


def _run_inspect(args: Namespace) -> None:
    """Inspects something in the CLI."""

    args.methods = args.methods or None
    args.dunder = args.dunder or None
    args.private = args.private or None

    target = (
        eval(args.inspect)  # pylint: disable=eval-used
        if args.eval
        else InspectorWindow.obj_from_path(args.inspect)
    )

    if not args.eval and isinstance(target, str):
        args.methods = False

    inspector = ptg.inspect(
        target,
        show_methods=args.methods,
        show_private=args.private,
        show_dunder=args.dunder,
    )

    ptg.terminal.print(inspector)


def _interpret_file(args: Namespace) -> None:
    """Interprets a PTG-YAML file."""

    with ptg.YamlLoader() as loader, open(args.file, "r", encoding="utf-8") as file:
        namespace = loader.load(file)

    if not args.print_only:
        with ptg.WindowManager() as manager:
            for widget in namespace.widgets.values():
                if not isinstance(widget, ptg.Window):
                    continue

                manager.add(widget)
        return

    for widget in namespace.widgets.values():
        for line in widget.get_lines():
            ptg.terminal.print(line)


def main(argv: list[str] | None = None) -> None:
    """Runs the program.

    Args:
        argv: A list of arguments, not included the 0th element pointing to the
            executable path.
    """

    _create_aliases()

    args = process_args(argv)

    args.app = args.app or (
        "getch"
        if args.getch
        else ("tim" if args.tim else ("color" if args.color else None))
    )

    if args.app or len(sys.argv) == 1:
        run_environment(args)
        return

    with ptg.terminal.record() as recording:
        if args.size:
            ptg.tim.print(f"{ptg.terminal.width}x{ptg.terminal.height}")

        elif args.version:
            _print_version()

        elif args.inspect:
            _run_inspect(args)

        elif args.exec:
            args.exec = sys.stdin.read() if args.exec == "-" else args.exec

            for name in dir(ptg):
                obj = getattr(ptg, name, None)
                globals()[name] = obj

            globals()["print"] = ptg.terminal.print

            exec(args.exec, locals(), globals())  # pylint: disable=exec-used

        elif args.highlight:
            text = sys.stdin.read() if args.highlight == "-" else args.highlight

            ptg.tim.print(ptg.highlight_python(text))

        elif args.file:
            _interpret_file(args)

        if args.export_svg:
            recording.save_svg(args.export_svg)

        elif args.export_html:
            recording.save_html(args.export_html)


if __name__ == "__main__":
    main(sys.argv[1:])
