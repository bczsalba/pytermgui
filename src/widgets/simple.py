from pytermgui import Widget


class MyWidget(Widget):
    render_count: int = 0

    def get_lines(self) -> list[str]:
        self.render_count += 1
        count = self.render_count

        return [f"I have been rendered {count} time{'s' if count > 1 else ''}!"]

&for line in MyWidget().get_lines():
&   print(line)

