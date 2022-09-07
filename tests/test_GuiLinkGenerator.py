from os.path import dirname, join

from viresclient import GuiLinkGenerator

TEST_DATA_DIR = join(dirname(__file__), "data")
TEST_FILE = join(TEST_DATA_DIR, "test_gui_workspace_config.json")


def test_from_file():
    link_gen = GuiLinkGenerator(
        "https://vires.services", server_type="Swarm", from_file=TEST_FILE
    )
    url = link_gen.url
    assert url.startswith("https://vires.services?ws=data%3Aapplication/json")


def test_config1():
    link_gen = GuiLinkGenerator("https://vires.services", "Swarm")
    link_gen.update_config(
        serviceVersion="3.9.0",
        timeSelection=["2022-08-30T00:00:00.000Z", "2022-08-30T01:30:00.000Z"],
        collections=["SW_OPER_MAGA_LR_1B"],
        parameter="F",
        satellites=["Alpha"],
    )
    assert isinstance(link_gen.config, dict)
    assert isinstance(link_gen.config_bytestring, bytes)
    url = link_gen.url
    assert url.startswith("https://vires.services?ws=data%3Aapplication/json")
