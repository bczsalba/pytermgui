import pytermgui as ptg


with ptg.YamlLoader() as loader, open("sandbox/common.yaml", "r") as config:
    namespace = loader.load(config)


with ptg.WindowManager() as manager:
    window = ptg.Window("hello")
    namespace.apply_to(window)
    manager += window
