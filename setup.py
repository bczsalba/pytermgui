from setuptools import setup, find_packages

setup(
    name="pytermgui",
    version="0.2.1",
    include_package_data=True,
    packages=["pytermgui", "pytermgui/widgets"],
    license="MIT",
    description="A simple and robust terminal UI library, written in Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[],
    python_requires=">=3.7.0",
    url="https://github.com/bczsalba/pytermgui",
    author="BcZsalba",
    author_email="bczsalba@gmail.com",
    entry_points={"console_scripts": ["ptg = pytermgui.cmd:main"]},
)
