You may have noticed the screenshots used throughout this documentation. Fun fact: They are all generated using the module! Some code is run, and its result is then displayed in an SVG image.

To do this, we use the [Termage](https://github.com/bczsalba/termage) module, which in turn uses the [Terminal.record](/reference/pytermgui/term#pytermgui.term.Terminal.record) method, and then calls [Recorder.export_svg](/reference/pytermgui/term#pytermgui.term.Recorder.export_svg) on the resulting terminal.

To use the recording & export API, simply enter a `Terminal.record` context, run some code & save the recording output:

```termage include=docs/src/exports1.py height=5
```

You can even hide the "window"'s title bar, and get a rectangular image with _just_ your code's output by specifying `chrome=False` while exporting:

<p style="padding-bottom: 5px;"></p>


```termage-svg chrome=false include=docs/src/exports1.py height=5
```

!!! note
    You can also export as plain HTML! We can't easily show it here (without manually pasting it in) since Termage and its plugin only wrap the SVG API.

For more information, check out the [Termage](https://github.com/bczsalba/termage) module!
