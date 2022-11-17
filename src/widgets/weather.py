from dataclasses import dataclass
from threading import Thread
from time import sleep

from pytermgui import Container, StyleManager, real_length, tim


@dataclass
class WeatherData:
    state: str
    wind: str
    clouds: str


class Weather(Container):
    # We want to retain the Container styles, so we merge in some new ones
    styles = StyleManager.merge(
        Container.styles,
        sunny="yellow",
        cloudy="grey",
        rainy="darkblue",
        snowy="snow",
        detail="245",
    )

    # Same story as above; unpacking into sets allows us to merge 2 dicts!
    chars = {
        **Container.chars,
        **{
            "sunny": "☀",
            "cloudy": "☁",
            "rainy": "☂",
            "snowy": "☃",
        },
    }

    def __init__(self, location: str, timeout: int, **attrs) -> None:
        super().__init__(**attrs)

        self.location = location
        self.timeout = timeout

&#        """
        Thread(target=self._monitor_loop, daemon=True).start()

&#        """
&        self.data = WeatherData("sunny", "15kph N/W", "scattered")
&        self.update_content()

    def _request_data(self) -> WeatherData:
&        return WeatherData("sunny", "15kph N/W", "scattered")
        ...

    def _monitor_loop(self) -> None:
        while True:
            self.data = self._request_data()
            self.update_content()
            sleep(self.timeout)

    def update_content(self) -> None:
        state = self.data.state

        style = self.styles[state]
        char = self._get_char(state)
        icon = style(char)

        self.set_widgets(
            [
                f"{icon} It is currently {state} in {self.location}. {icon}",
                "",
                f"{self.styles.detail('Wind')}: {self.data.wind}",
                f"{self.styles.detail('Clouds')}: {self.data.clouds}",
            ]
        )


&widget = Weather("Los Angeles", 1, static_width=60)
&for line in widget.get_lines():
&    print(line)
&termage.fit(widget)
