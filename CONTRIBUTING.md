# Contributing

## Formatting

pytermgui uses different formatters to keep the code consistent and improve readability.
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
It is common for developers to configure their IDEs to automatically format files as they are saved.

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

pytermgui uses [pylint](https://github.com/PyCQA/pylint) to lint our code.

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
