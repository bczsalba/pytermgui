from dataclasses import dataclass

from pytermgui import (
    WindowManager,
    Window,
    Container,
    Splitter,
    InputField,
    Button,
    VerticalAlignment,
    keys,
)


@dataclass
class Person:
    lastname: str
    firstname: str

    def __str__(self) -> None:
        return f"{self.firstname}, {self.lastname}"


DATABASE: list[Person] = [
    Person("Emil", "Hans"),
    Person("Mustermann", "Max"),
    Person("Tisch", "Roman"),
]

with WindowManager() as manager:
    results = Container()
    fltr = InputField(prompt="Filter prefix: ")

    def fill_results() -> None:
        results.set_widgets(
            [
                str(person)
                for person in DATABASE
                if person.lastname.lower().startswith(fltr.value.lower())
            ]
        )

    fltr.bind(keys.ANY_KEY, lambda *_: fill_results())

    fill_results()
    firstname = InputField(prompt="First name: ")
    lastname = InputField(prompt="Last name:  ")

    manager.layout.add_slot()
    manager.add(
        Window(
            Container(
                fltr,
                results,
            ),
            Container(
                "",
                firstname,
                lastname,
                "",
                Button("Create"),
                Button("Update"),
                Button("Delete"),
            ),
            vertical_align=VerticalAlignment.TOP,
        )
        .center()
        .set_title("[secondary bold]CRUD")
    )
