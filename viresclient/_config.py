#-------------------------------------------------------------------------------
#
# Configuration file handling.
#
# Authors: Ashley Smith <ashley.smith@ed.ac.uk>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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

from io import StringIO
from os import name as os_name, chmod
from os.path import expanduser, join
from configparser import ConfigParser

DEFAULT_CONFIG_PATH = join(expanduser("~"), ".viresclient.ini")


class ClientConfig():
    """ Client configuration.

    Example usage:

    >> cc = ClientConfig()      # use default configuration file
    >> cc = ClientConfig("./viresconf.ini")  # use custom configuration file

    >> print(cc.path)           # print path
    >> print(cc)                # print  whole configuration

    >> cc.default_url = "https://foo.bar/ows"  # set default server

    # access credentials configuration ...
    >> cc.set_site_config("https://foo.bar/ows", username="...", password="...")
    >> cc.set_site_config("https://foo2.bar/ows", token="...")

    >> cc.save()    # save configuration

    """

    def __init__(self, path=None):
        self._path = path or DEFAULT_CONFIG_PATH
        self._config = ConfigParser()
        self._config.read(self._path)

    @property
    def path(self):
        """ Get path of the configuration file. """
        return self._path

    @property
    def default_url(self):
        """ Get default URL or None if not set. """
        return self._get_section('default').get('url')

    @default_url.setter
    def default_url(self, value):
        """ Set default URL. """
        self._update_section('default', url=value)

    @default_url.deleter
    def default_url(self):
        """ Unset the default URL. """
        self._update_section('default', url=None)

    def set_site_config(self, url, **options):
        """ Set configuration for the given URL. """
        self._set_section(url, **options)

    def get_site_config(self, url):
        """ Get configuration for the given URL. """
        return dict(self._get_section(url))

    def _update_section(self, section, **options):
        """ Update configuration file section. """
        all_options = dict(self._get_section(section))
        all_options.update(options)
        self._set_section(section, **all_options)

    def _get_section(self, section):
        try:
            return self._config[section]
        except KeyError:
            return {}

    def _set_section(self, section, **options):
        """ Set configuration file section. """
        options = {
            key: value
            for key, value in options.items() if value is not None
        }
        if options:
            self._config[section] = options
        else:
            self._delete_section(section)

    def _delete_section(self, section):
        """ Delete configuration file section. """
        try:
            del self._config[section]
        except KeyError:
            pass

    def save(self):
        """ Save the configuration file. """
        with open(self._path, 'w') as file_:
            self._config.write(file_)
            # make file private
            if os_name == 'posix':
                chmod(file_.fileno(), 0o0600)

    def __str__(self):
        """ Dump configuration to a string. """
        fobj = StringIO()
        self._config.write(fobj)
        return fobj.getvalue()
