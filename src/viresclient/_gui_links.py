from __future__ import annotations

import json
from base64 import standard_b64encode
from gzip import GzipFile
from io import BytesIO
from urllib.parse import quote

from viresclient._data import GUI_WORKSPACE_CONFIG_SWARM


class GuiLinkGenerator:
    """Generate URLs to instantiate the GUI with given settings

    Examples:

        Using manual configuration::

            link_gen = GuiLinkGenerator("https://vires.services", "Swarm")
            link_gen.update_config(
                serviceVersion="3.9.0",
                timeSelection=["2022-08-30T00:00:00.000Z", "2022-08-30T01:30:00.000Z"],
                collections=["SW_OPER_MAGA_LR_1B"],
                parameter="F",
                satellites=["Alpha"]
            )
            print(link_gen.url)

        Using a workspace file exported from the GUI::

            link_gen = GuiLinkGenerator("https://vires.services", "Swarm", file)
            print(link_gen.url)
    """

    def __init__(self, base_url: str, server_type: str = "Swarm", from_file=None):
        self.base_url = base_url
        self.server_type = server_type
        if server_type == "Swarm":
            self.config = GUI_WORKSPACE_CONFIG_SWARM
        else:
            raise NotImplementedError
        if from_file:
            with open(from_file) as file_in:
                self.config = json.load(file_in)

    @property
    def config_bytestring(self):
        return json.dumps(self.config).encode("ascii")

    def update_config(self, **options):
        """Update the configuration given a set of options

        Expected options for Swarm, example::

            serviceVersion="3.9.0",
            timeSelection=["2022-08-30T00:00:00.000Z", "2022-08-30T01:30:00.000Z"],
            collections=["SW_OPER_MAGA_LR_1B"],
            parameter="F",
            satellites=["Alpha"]

        """
        if self.server_type == "Swarm":
            self.config = self._build_config_swarm(self.config, **options)
        else:
            raise NotImplementedError

    @staticmethod
    def _build_config_swarm(
        json_data: dict,
        serviceVersion: str = "NULL",
        timeSelection: tuple[str] = ("NULL", "NULL"),
        collections: tuple[str] = ("NULL"),
        parameter: str = "NULL",
        satellites: tuple[str] = ("NULL"),
    ) -> str:
        json_data["serviceVersion"] = serviceVersion
        json_data["timeSelection"] = timeSelection
        json_data["productsConfiguration"] = {
            collection: {"visible": True} for collection in collections
        }
        # Web client always requires MAGA to be set
        if "SW_OPER_MAGA_LR_1B" not in json_data["productsConfiguration"]:
            json_data["productsConfiguration"]["SW_OPER_MAGA_LR_1B"] = {
                "visible": False
            }
        json_data["plotConfiguration"][0]["yAxis"] = [parameter]
        for satellite in ("Alpha", "Bravo", "Charlie", "NSC", "Upload"):
            json_data["satellites"][satellite] = satellite in satellites
        return json_data

    @property
    def url(self):
        quoted_data_url = get_shortest_quoted_data_url(
            self.config_bytestring,
            [
                get_data_url_json_base64_gzip,
                get_data_url_json_base64,
                get_data_url_json,
            ],
        )
        return f"{self.base_url}?ws={quoted_data_url}"


def get_shortest_quoted_data_url(config, encoders):
    return sorted(
        (len(data), data) for data in (quote(encoder(config)) for encoder in encoders)
    )[0][1]


def get_data_url_json_base64_gzip(config):
    return "data:application/json+gzip;base64," + (
        standard_b64encode(gzip_data(config)).decode("ascii")
    )


def get_data_url_json_base64(config):
    return "data:application/json;base64," + (
        standard_b64encode(config).decode("ascii")
    )


def get_data_url_json(config):
    return "data:application/json," + config.decode("ascii")


def gzip_data(data):
    buffer_ = BytesIO()
    with GzipFile(fileobj=buffer_, mode="wb", compresslevel=9) as file_gzip:
        file_gzip.write(data)
        file_gzip.close()
    buffer_.seek(0)
    return buffer_.read()
