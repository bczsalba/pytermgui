import pytermgui as ptg


def test_auto_label():
    obj = ptg.Widget.from_data("hello")

    assert isinstance(obj, ptg.Label)
    assert obj.value == "hello"


def test_auto_splitter():
    items = {ptg.Label("hello"), ptg.Button("there")}

    obj = ptg.Widget.from_data(tuple(items))

    assert isinstance(obj, ptg.Splitter)
    assert set(obj._widgets) == items


def test_auto_button():
    def _callback(btn: ptg.Button) -> None:
        return None

    obj = ptg.Widget.from_data(["Label", _callback])

    assert isinstance(obj, ptg.Button)
    assert obj.onclick is _callback
    assert obj.label == "Label"


def test_auto_checkbox():
    obj = ptg.Widget.from_data([True])

    assert isinstance(obj, ptg.Checkbox)
    assert obj.checked == True


def test_auto_toggle():
    obj = ptg.Widget.from_data([("One", "Two")])

    assert isinstance(obj, ptg.Toggle)
    assert obj.label == "One"


def _test_prompt(obj: ptg.Splitter, left: ptg.Label, right: ptg.Label):
    assert isinstance(obj, ptg.Splitter)
    assert isinstance(obj[0], ptg.Label) and obj[0].value == left.value
    assert isinstance(obj[1], ptg.Label) and obj[1].value == right.value


def test_auto_prompt():
    left = ptg.Label("Key")
    right = ptg.Label("Value")
    obj = ptg.Widget.from_data({left: right})

    _test_prompt(obj, left, right)


def test_auto_prompt_multirow():
    items = {"One": "Two", "Three": "Four", "Five": "Six"}
    rows = ptg.Widget.from_data(items)

    for row, (left, right) in zip(rows, items.items()):
        _test_prompt(row, ptg.Label(left), ptg.Label(right))


def test_auto_bad_object():
    assert ptg.Widget.from_data(1) is None
