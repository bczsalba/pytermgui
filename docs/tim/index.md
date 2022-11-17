PyTermGUI offers a markup language complimentary to the other features of the library, named **T**erminal **I**nline **M**arkup, or **TIM** for short. This language is in use in various places within the library, and is supported by pretty much everything we offer that displays text.

```python
--8<-- "docs/src/tim/index.py"
```


```termage-svg include=docs/src/tim/index.py title=TIM\ Example height=4
```

## Philosophy

- **Convenience**

    Raw ANSI sequences are cumbersome to use and hard to read/write. TIM aims to improve this by assigning easy-to-read names to pretty much all ANSI syntax.

- **Speed**

    Since this language is meant to be used in performance-critical applications, it must be pretty fast. As of 16th of July 2022, TIM is magnitudes faster than [Rich](https://github.com/textualize/rich)'s own markup language, the only "competition" I know about.

    This is achieved mostly by smart caching routines, as well as a tightly written parsing algorithm.

- **Extensibility**

    I like tinkering. I hate using things that are made with the philosophy of "this is what I made, and it's all that you will get.". TIM implements customizability in its [alias](usage/#alias) and [macro](usage/#macros) systems.

- **Convenience & granularity**

    Above all, TIM was made to be simple and ergonomic to use. Styles follow their most-commonly used names, and every tag is applied as its own distinct entity, and aren't joined into a set style. This allows you to specifically clear certain tags, while not touching the rest of the style.
