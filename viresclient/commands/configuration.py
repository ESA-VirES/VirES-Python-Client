#-------------------------------------------------------------------------------
#
# viresclient CLI - configuration management commands
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

import sys
from getpass import getpass, getuser
from os.path import exists
from viresclient import ClientConfig
from .common import ConfigurationCommand, UrlConfigurationCommand


class InitializeConfigurationCommand(ConfigurationCommand):
    help = (
        "Initialize client configuration from VIRES_ACCESS_CONFIG "
        "environment variable. "
        "Intended to be used for VRE client initialization."
    )

    def execute(self, config_path):
        config = ClientConfig(path=config_path)
        config.init()
        config.save()


class SetTokenCommand(UrlConfigurationCommand):
    help = "Set an access token for the given server URL."

    def add_arguments_to_parser(self, parser):
        super().add_arguments_to_parser(parser)
        parser.add_argument(
            "token", action="store", nargs="?", type=str, help="access token"
        )

    def execute(self, config_path, server_url, token):
        if token is None:
            token = input("Enter access token: ")
        config = ClientConfig(path=config_path)
        config.set_site_config(server_url, token=token)
        config.save()


class SetPasswordCommand(UrlConfigurationCommand):
    help = "Set username and password for the given server URL."

    def add_arguments_to_parser(self, parser):
        super().add_arguments_to_parser(parser)
        parser.add_argument(
            "username", action="store", nargs="?", type=str, help="username"
        )
        parser.add_argument(
            "password", action="store", nargs="?", type=str, help="password"
        )

    def execute(self, config_path, server_url, username, password):
        config = ClientConfig(path=config_path)

        if username is None:
            default_username = (
                config.get_site_config(server_url).get("username") or getuser()
            )
            username = input(
                "Enter username [%s]: " % default_username
            ) or default_username

        if password is None:
            password = getpass("Enter password: ")

        config.set_site_config(server_url, username=username, password=password)
        config.save()


class RemoveServerCommand(UrlConfigurationCommand):
    help = "Remove any stored configuration for the given server URL."

    def execute(self, config_path, server_url):
        config = ClientConfig(path=config_path)
        config.set_site_config(server_url)
        config.save()


class SetDefaultServerCommand(UrlConfigurationCommand):
    help = "Set the default server URL."

    def execute(self, config_path, server_url):
        config = ClientConfig(path=config_path)
        config.default_url = server_url
        config.save()


class RemoveDefaultServerCommand(ConfigurationCommand):
    help = "Remove the default server URL."

    def execute(self, config_path):
        config = ClientConfig(path=config_path)
        config.default_url = None
        config.save()


class ShowConfigurationCommand(ConfigurationCommand):
    """ Command dumping configuration to a standard output. """
    help = "Print the configuration to standard output."

    def execute(self, config_path):
        config = ClientConfig(path=config_path)
        if not exists(config.path):
            raise self.Error(
                "Configuration file %s does not exist!" % config.path
            )
        sys.stdout.write(str(config))
