#-------------------------------------------------------------------------------
#
# viresclient CLI - data upload commands
#
# Project: VirES-Python-Client
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
# pylint: disable=missing-docstring,arguments-differ

from os.path import exists
from viresclient import ClientConfig
from .common import ConfigurationCommand
from .._api.upload import DataUpload


JSON_OPTS = {'sort_keys': False, 'indent': 2, 'separators': (',', ': ')}


class DataUploadCommand(ConfigurationCommand):
    """ Base data upload command. """

    def add_arguments_to_parser(self, parser):
        super().add_arguments_to_parser(parser)
        parser.add_argument(
            "server_url", action="store", nargs="?", type=str, help="server URL"
        )

    def get_data_upload_instance(self, config_path, server_url):
        """ Get instance of the DataUpload class. """
        config = ClientConfig(path=config_path)
        server_url = server_url or config.default_url

        if not server_url:
            raise self.Error(
                "No default URL is configured. "
                "Enter server URL as a CLI argument!"
            )

        api_url = DataUpload.get_api_url(server_url)
        ows_url = DataUpload.get_ows_url(server_url)
        access_token = config.get_site_config(ows_url).get('token')

        if not access_token:
            raise self.Error("No access token configured for %s!" % ows_url)

        return DataUpload(api_url, token=access_token)


class UploadDataFileCommand(DataUploadCommand):
    help = """ Upload data file. """

    def add_arguments_to_parser(self, parser):
        super().add_arguments_to_parser(parser)
        parser.add_argument(
            "filename", action="store", type=str, help="uploaded file"
        )

    def execute(self, config_path, server_url, filename):

        if not exists(filename):
            raise self.Error("File %s does not exist!" % filename)

        api_proxy = self.get_data_upload_instance(config_path, server_url)

        item = api_proxy.post(filename)
        print("%s[%s] uploaded" % (item['identifier'], item['filename']))


class RemoveUploadsCommand(DataUploadCommand):
    help = """ Remove uploaded file. """

    def execute(self, config_path, server_url):
        api_proxy = self.get_data_upload_instance(config_path, server_url)
        for item in api_proxy.get():
            api_proxy.delete(item['identifier'])
            print("%s[%s] removed" % (item['identifier'], item['filename']))


class SetConstantParameters(DataUploadCommand):
    help = """ Set constant parameters. """

    def add_arguments_to_parser(self, parser):
        super().add_arguments_to_parser(parser)
        parser.add_argument(
            "-p", "--parameter", action="append", type=str,
            help="key=value parameter"
        )

    def execute(self, config_path, server_url, parameter):
        if not parameter:
            return # nothing to be done

        new_parameters = dict(self._parse_parameter(item) for item in parameter)

        api_proxy = self.get_data_upload_instance(config_path, server_url)
        for item in api_proxy.get():
            if item.get("constant_fields") is not None:
                parmeters = {
                    field: data['value']
                    for field, data in item["constant_fields"].items()
                }
                parmeters.update(new_parameters)
                api_proxy.set_constant_parameters(
                    item['identifier'], parmeters, replace=True
                )
                print("%s: parameters updated" % (item['identifier']))

            else:
                raise self.Error(
                    "Constant parameters not supported by the old server API."
                )

    @classmethod
    def _parse_parameter(cls, raw_parameter):
        name, assignment, value = raw_parameter.partition("=")
        name = name.strip()
        try:
            if assignment != "=" or not value or not name:
                raise ValueError
            return name, float(value)
        except ValueError:
            raise cls.Error(
                "Invalid parameter specification '%s' !" % raw_parameter
            )

class RemoveConstantParameters(DataUploadCommand):
    help = """ Remove constant parameters. """

    def execute(self, config_path, server_url):
        api_proxy = self.get_data_upload_instance(config_path, server_url)
        for item in api_proxy.get():
            if item.get("constant_fields"):
                api_proxy.set_constant_parameters(
                    item['identifier'], {}, replace=True
                )
                print("%s: parameters removed" % (item['identifier']))


class ShowUploadsCommand(DataUploadCommand):
    help = """ Print info about the uploaded file. """

    def execute(self, config_path, server_url):
        api_proxy = self.get_data_upload_instance(config_path, server_url)
        for item in api_proxy.get():
            self.print_info(item)

    @staticmethod
    def print_info(info):
        print(info['identifier'])
        print("  filename:     ", info['filename'])
        print("  is valid:     ", info.get('is_valid', True))
        print("  data start:   ", info['start'])
        print("  data end:     ", info['end'])
        print("  uploaded on:  ", info['created'])
        print("  content type: ", info['content_type'])
        print("  size:         ", info['size'])
        print("  MD5 checksum: ", info['checksum'])

        missing_fields = info.get("missing_fields", {})
        if missing_fields:
            print("  missing mandatory fields:")
            for field in sorted(list(missing_fields)):
                print("    %s" % field)

        constant_fields = info.get("constant_fields", {})
        if constant_fields:
            print("  constant fields:")
            for field, data in sorted(constant_fields.items()):
                print("    %s=%s" % (field, data['value']))

        print("  fields:")
        for field in sorted(info.get('fields') or info.get('info') or []):
            print("    %s" % field)
