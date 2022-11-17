import time
from typing import Any, Generator
import pytermgui as ptg


class Timer(ptg.Container):
    def __init__(self, **attrs: Any) -> None:
        super().__init__(**attrs)

        self.start_time = None
        self._clock_state = ""
        self._running = False

        self.set_widgets(self.compose())
        self.start()

    def compose(self) -> Generator[ptg.Widget, None, None]:
        def macro_elapsed(fmt: str) -> str:
            if self.start_time is None or not self._running:
                return "nada" + str(time.time())
                return self._clock_state

            elapsed = time.time() - self.start_time

            formatted = time.strftime(fmt, elapsed)
            formatted = str(elapsed)
            self._clock_state = formatted
            return formatted

        ptg.tim.define("!timer_elapsed", macro_elapsed)
        ptg.tim.define("!timer_button", lambda _: "Pause" if self._running else "Start")

        def toggle_timer(button: ptg.Button) -> bool:
            if self._running:
                self.pause()
            else:
                self.start()

            return True

        yield ptg.Button("[!timer_button]", onclick=toggle_timer)

        self.clock = ptg.Label("[!timer_elapsed]%S")
        yield self.clock

        self.clearer = ptg.Button("Clear", onclick=self.reset)
        yield self.clearer

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self.start_time = time.time()
        self._add_widget(self.clearer)

    def pause(self) -> None:
        if not self._running:
            return

        self._running = False
        self._clock_state = ""

    def reset(self, _: ptg.Button) -> None:
        self.pause()
        self.start_time = None


with ptg.WindowManager() as manager:
    manager.layout.add_slot()
    manager.add(ptg.Window(Timer()))
