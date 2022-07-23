"""Project setup.

Most of the metadata comes from `pyproject.toml`.

This file is for:

- Adding in the remaining, non-supported bits of data
- Support of `pip install -e`
- Support for GitHub's dependency indexing
"""

from setuptools import setup

# These two fields aren't supported properly by setuptools' pyproject.toml
# reading, so we'll add it manually.
setup(author="Balázs Cene", url="https://github.com/bczsalba/PyTermGUI")
