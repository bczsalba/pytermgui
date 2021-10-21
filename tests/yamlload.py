import pytermgui as ptg


def main() -> None:
    """Main method"""

    # ptg.Splitter.set_style("separator", ptg.MarkupFormatter("[@234 grey]{item}"))
    with open("tests/environment.yaml", "r") as file:
        namespace = ptg.YamlLoader().load(file)

    with ptg.WindowManager() as manager:
        crit_window = namespace.CriteriaWindow
        manager.add(crit_window)

        manager.run()


if __name__ == "__main__":
    main()
