#-------------------------------------------------------------------------------
#
# viresclient CLI
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
import logging
from argparse import ArgumentParser
from .common import Command
from .configuration import (
    SetTokenCommand, SetPasswordCommand, RemoveServerCommand,
    SetDefaultServerCommand, RemoveDefaultServerCommand,
    ShowConfigurationCommand, InitializeConfigurationCommand,
)
from .upload import (
    UploadDataFileCommand, ShowUploadsCommand, RemoveUploadsCommand,
    RemoveConstantParameters, SetConstantParameters,
)

# dictionary of registered commands
COMMANDS = {
    # configuration commands
    "set_token": SetTokenCommand(),
    "set_password": SetPasswordCommand(),
    "remove_server": RemoveServerCommand(),
    "set_default_server": SetDefaultServerCommand(),
    "remove_default_server": RemoveDefaultServerCommand(),
    "show_configuration": ShowConfigurationCommand(),
    # data upload commands
    "upload_file": UploadDataFileCommand(),
    "show_uploads": ShowUploadsCommand(),
    "clear_uploads": RemoveUploadsCommand(),
    "clear_upload_parameters": RemoveConstantParameters(),
    "set_upload_parameters": SetConstantParameters(),
    # automatic configuration initialization
    "init_configuration": InitializeConfigurationCommand(),
}


def main(*cli_args):
    """ main function. """
    parser = ArgumentParser()

    # add registered subcommands
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # NOTE: .add_subparsers() in Python < 3.7 does not support the 'required'
    # parameter and it has to be set as an object property.
    subparsers.required = True

    for command_name, command in COMMANDS.items():
        command_parser = subparsers.add_parser(command_name, help=command.help)
        command.add_arguments_to_parser(command_parser)

    # parse CLI arguments
    parsed_args = dict(parser.parse_args(args=cli_args[1:]).__dict__)

    # execute selected subcommand
    requested_command = parsed_args.pop('command')
    return COMMANDS[requested_command].execute(**parsed_args)


def start():
    try:
        sys.exit(main(*sys.argv))
    except Command.Error as error:
        print("ERROR: %s" % error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    start()
