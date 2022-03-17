import pytest
from pathlib import Path
from pytermgui import FileLoader, JsonLoader, YamlLoader, prettifiers

# TODO: Once dumping is once again more supported that should be included
#       here as well.


class BaseLoaderTester:

    path: Path
    loader: FileLoader

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.loader = type(self).loader()

        with self.loader as loader, open(self.path) as yaml:
            self.namespace = loader.load(yaml)

    def test_namespace_widget_length(self):
        assert len(self.namespace.widgets) == 1


class TestYamlLoader(BaseLoaderTester):
    loader = YamlLoader
    path = Path("tests/test.yaml")


class TestJsonLoader(BaseLoaderTester):
    loader = JsonLoader
    path = Path("tests/test.json")
