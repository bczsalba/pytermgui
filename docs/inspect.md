PyTermGUI provides a pretty nifty inspection utility, `inspect`! It's useful to figure out the signature of functions, inspect their general shape & docstrings.

```termage-svg include=docs/src/inspect1.py width=100
```

The easiest way to use it is by running `ptg -i` or `ptg --inspect` with a fully qualified name. This will create an [Inspector](/reference/pytermgui/inspector#pytermgui.inspector.Inspector) object for the given name, and print it.

You can also give the same function an expression to evaluate. This might be useful if you want to know the type & methods of an object that is the result of some function or method.

The more general way to access the API is by using the [inspect](/reference/pytermgui/inspector#pytermgui.inspector.inspect) function from within Python. You can give it _any_ object, and it will give you as much information as it can found out from the signature & source code. You can also play around with an interactive version of the tool by running `ptg --app inspect`, which will give you a nice UI to play around with.

```termage-svg include=docs/src/inspect2.py
```
