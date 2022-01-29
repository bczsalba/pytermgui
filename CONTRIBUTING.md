# Contributing

Thank you for taking the interest to contribute! There is always aspects of the library we can improve, so any contributions are welcome!

## Our tooling

If you're only here to find out what programs you need to use when contributing, here is a list:

### Python-based

- [black](https://github.com/psf/black) - Python code formatter
- [pylint](https://github.com/PyCQA/pylint) - Python linter
- [mypy](https://github.com/python/mypy) - Static type checker

### Other

- [prettier](https://github.com/prettier/prettier) - Formatter for various other formats

For a more detailed description on why each of these are needed, scroll down to their specific sections.

## When should you contribute?

### Found an issue you could fix?

Make sure no one has already started working on it. Once you do start working, it is good to add a comment to the issue to notify others.

### No issue raised?

You don't wanna work hours on code only for it to be thrown out because the maintainers didn't agree with it. To avoid doing so, raise an issue about your ideas.

## How should you contribute?

### Make sure your contribution has a reason.

If you aren't fixing a reported issue, start by raising a ticket yourself to make sure your changes are wanted.

### Use descriptive, imperative commit messages.

Commit frequently, with each commit following a single major theme. Commits like `made some changes` will **not** be accepted.

For your commit message, use a style that describes what it is _going to do_, not what it has already done.

For example:

```bash
added a new slider widget  # Bad
Add a new slider widget  # Good!
```

It is also important to capitalize the first letter of the text, and to not append a period to the end. Standard committing rules (50 character title, empty line separating title from body) apply.

### Follow the rest of the guideline below

We take code style very seriously. Your code should use and apply the tooling describe below, otherwise we cannot accept it.

## Formatting

PyTermGUI uses different formatters to keep the code consistent and improve readability.
Here are the formatters you need on your system to contribute to pytermgui:

|                                        Formatter | Files                  |
| -----------------------------------------------: | :--------------------- |
| [prettier](https://github.com/prettier/prettier) | `.md`, `.yml`, `.yaml` |
|            [black](https://github.com/psf/black) | `.py`                  |

### Installation

prettier:

1. Install nodejs and npm (npx comes with it)

black:

1. Install python and pip
2. Run the following command

   ```bash
   pip install black
   ```

### Usage

Run these commands to format your files.

It is common for developers to configure their IDEs to automatically format files as they are saved. See each tool for instructions on how to do so.

**WARNING**: These commands will overwrite your files.

prettier:

```bash
npx prettier --write .
```

black:

```bash
black .
```

## Linting

PyTermGUI uses [pylint](https://github.com/PyCQA/pylint) to ensure any code is up to our standards. Any pushed code will be tested against the program in a GitHub action, and your changes will **not** be merged as long as the score is below 10.0.

### Installation

1. Install python and pip
2. Run the following command
   ```bash
   pip install pylint
   ```

### Usage

```bash
pylint pytermgui
```

## Typing

PyTermGUI uses Python's type hint system to improve readability and code stability. For this, we use the [mypy](https://github.com/python/mypy) static type checker. Your code needs to pass mypy with no errors in order to be merged.

### Installation

1. Install python and pip
2. Install mypy using the following command
   ```bash
   pip install mypy
   ```

### Usage

```bash
mypy pytermgui
```
