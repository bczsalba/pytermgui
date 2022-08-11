"""Project setup.

Most of the metadata comes from `pyproject.toml`.

This file is for:

- Adding in the remaining, non-supported bits of data
- Support of `pip install -e`
- Support for GitHub's dependency indexing
"""

from setuptools import setup

# These fields aren't supported properly by setuptools' pyproject.toml
# reading, so we'll add it manually.
#
# `name` is needed for GitHub's dependency tracking to function properly.
setup(
    name="pytermgui", author="Balázs Cene", url="https://github.com/bczsalba/PyTermGUI"
)
