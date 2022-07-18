from setuptools import find_packages, setup

import pytermgui

setup(
    name="pytermgui",
    version=pytermgui.__version__,
    include_package_data=True,
    package_data={
        "pytermgui": ["py.typed"],
    },
    packages=find_packages(),
    license="MIT",
    description="A simple and robust terminal UI library, written in Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["typing_extensions"],
    python_requires=">=3.7.0",
    url="https://github.com/bczsalba/pytermgui",
    author="BcZsalba",
    author_email="bczsalba@gmail.com",
    entry_points={"console_scripts": ["ptg = pytermgui.cmd:main"]},
)
