from __future__ import annotations

import sys
import json
from io import BytesIO
from gzip import GzipFile
from urllib.parse import quote
from base64 import standard_b64encode

from viresclient._data import GUI_WORKSPACE_CONFIG_SWARM


class GuiLinkGenerator:
    """Generate URLs to instantiate the GUI with given settings

    Examples:

        ::
            link_gen = GuiLinkGenerator("https://vires.services", "Swarm")
            link_gen.update_config(
                serviceVersion="3.9.0",
                timeSelection=["2022-08-30T00:00:00.000Z", "2022-08-30T01:30:00.000Z"],
                collection="SW_OPER_MAGA_LR_1B",
                parameter="F",
                satellites=["Alpha"]
            )
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
    def config_string(self):
        return json.dumps(self.config).encode('ascii')

    def update_config(self, **options):
        """Update the configuration given a set of options

        Expected options for Swarm, example::

            serviceVersion="3.9.0",
            timeSelection=["2022-08-30T00:00:00.000Z", "2022-08-30T01:30:00.000Z"],
            collection="SW_OPER_MAGA_LR_1B",
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
        timeSelection: list[str] = ["NULL", "NULL"],
        collection: str = "NULL",
        parameter: str = "NULL",
        satellites: list[str] = ["NULL"],
    ) -> str:
        json_data["serviceVersion"] = serviceVersion
        json_data["timeSelection"] = timeSelection
        json_data["productsConfiguration"] = {collection: {}}
        json_data["plotConfiguration"][0]["yAxis"] = [parameter]
        for satellite in ("Alpha", "Bravo", "Charlie", "NSC", "Upload"):
            json_data["satellites"][satellite] = satellite in satellites
        return json_data

    @property
    def url(self):
        quoted_data_url = get_shortest_quoted_data_url(
            self.config_string,
            [
                get_data_url_json_base64_gzip,
                get_data_url_json_base64,
                get_data_url_json,
            ]
        )
        return f"{self.base_url}?ws={quoted_data_url}"


def get_shortest_quoted_data_url(config, encoders):
    return sorted([
        (len(data), data) for data
        in (quote(encoder(config)) for encoder in encoders)
    ])[0][1]


def get_data_url_json_base64_gzip(config):
    return "data:application/json+gzip;base64," + (
        standard_b64encode(gzip_data(config)).decode('ascii')
    )


def get_data_url_json_base64(config):
    return "data:application/json;base64," + (
        standard_b64encode(config).decode('ascii')
    )


def get_data_url_json(config):
    return "data:application/json," + config.decode('ascii')


def gzip_data(data):
    buffer_ = BytesIO()
    with GzipFile(fileobj=buffer_, mode="wb", compresslevel=9) as file_gzip:
        file_gzip.write(data)
        file_gzip.close()
    buffer_.seek(0)
    return buffer_.read()


def main():
    link_gen = GuiLinkGenerator("https://vires.services", "Swarm")
    link_gen.update_config(
        serviceVersion="3.9.0",
        timeSelection=["2022-08-30T00:00:00.000Z", "2022-08-30T01:30:00.000Z"],
        collection="SW_OPER_MAGA_LR_1B",
        parameter="F",
        satellites=["Alpha"]
    )
    print(link_gen.url)


if __name__ == "__main__":
    # sys.exit(main(sys.argv[1], sys.argv[2]))
    sys.exit(main())
