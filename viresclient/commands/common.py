#-------------------------------------------------------------------------------
#
# viresclient CLI - data upload
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


class Command():
    """ Base command class. """
    help = None #command help

    class Error(Exception):
        """ Generic command error exception. """

    def add_arguments_to_parser(self, parser):
        raise NotImplementedError

    def execute(self, **kwargs):
        raise NotImplementedError


class ConfigurationCommand(Command):
    """ Base class for commands working with a configuration file. """

    def add_arguments_to_parser(self, parser):
        parser.add_argument(
            "-c", "--config", action="store", type=str, dest="config_path",
            help="Path to a configuration file."
        )


class UrlConfigurationCommand(ConfigurationCommand):
    """ Base class for commands working with a URL configuration file. """

    def add_arguments_to_parser(self, parser):
        super().add_arguments_to_parser(parser)
        parser.add_argument(
            "server_url", action="store", type=str, help="server URL"
        )
