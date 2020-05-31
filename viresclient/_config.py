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

import os
import json
from io import StringIO
from os.path import expanduser, join
from getpass import getpass
from configparser import ConfigParser
from ._api.token import TokenManager

# Identify whether code is running in Jupyter notebook or not
try:
    from IPython import get_ipython
    from IPython.display import display_html
    IN_JUPYTER = 'zmqshell' in str(type(get_ipython()))
    from IPython.core.error import StdinNotImplementedError
except ImportError:
    IN_JUPYTER = False


DEFAULT_CONFIG_PATH = join(expanduser("~"), ".viresclient.ini")
DEFAULT_INSTANCE_NAME = "VirES Python Client"
DEFAULT_SERVER = "https://vires.services"
DATA_API_PATH = "/ows"
TOKEN_GUI_PATH = "/accounts/tokens/"


def _get_ows_url(url):
    """ https//foo.bar(/ows)? -> https//foo.bar/ows """
    return TokenManager.RE_URL_BASE.sub(DATA_API_PATH, url, count=1)


def _get_token_gui_url(url):
    """ https//foo.bar(/ows)? -> https//foo.bar/accounts/tokens/ """
    return TokenManager.RE_URL_BASE.sub(TOKEN_GUI_PATH, url, count=1)


def set_token(url="https://vires.services/ows", token=None, set_default=False):
    """ Set the access token for a given URL, using user input.

    Get an access token at https://vires.services/accounts/tokens/

    See https://viresclient.readthedocs.io/en/latest/config_details.html

    This will create a configuration file if not already present, and input a
    token configuration for a given URL, replacing the current token. It sets
    the given URL as the default if one is not already set. It uses getpass to
    hide the token from view.

    Example usage::

      set_token()
      # user prompted for input of token, for https://vires.services/ows

      set_token(url="https://vires.services/ows")
      # user prompted for input of token, for given url

      set_token(url="https://vires.services/ows", token="...")
      # set a given url and token (no prompting)

    """
    if not token:
        url4token = _get_token_gui_url(url)
        # Provide user with information on token setting URL
        # Nicer output in IPython, with a clickable link
        if IN_JUPYTER:
            def _linkify(_url):
                if _url:
                    return '<a href="{url}">{url}</a>'.format(url=_url)
                return '(link not found)'
            display_html(
                'Setting access token for {}...<br>'.format(url)
                + 'Generate a token at {}'.format(_linkify(url4token)),
                raw=True)
        else:
            print('Setting access token for', url, ' ...')
            url4token = url4token if url4token else '(link not found)'
            print('Generate a token at', url4token)
        # Prompt user to supply token, if input is allowed
        try:
            token = getpass('Enter token:')
        except EOFError:
            # getpass is meant to do something like this as a fallback
            # but it fails with EOFError in Jupyter (rare glitch)
            # https://github.com/ESA-VirES/VirES-Python-Client/issues/46
            token = input('Enter token:')
        except StdinNotImplementedError:
            print('No input method available. Unable to set token.')
            return
    config = ClientConfig()
    config.set_site_config(url, token=token)
    # Use the current URL as default if none has been set before
    if (not config.default_url) or set_default:
        config.default_url = url
    config.save()
    print("Token saved for", url)


class ClientConfig():
    """ Client configuration.

    Example usage::

      cc = ClientConfig()      # use default configuration file
      cc = ClientConfig("./viresconf.ini")  # use custom configuration file

      print(cc.path)           # print path
      print(cc)                # print the whole configuration

      cc.default_url = "https://foo.bar/ows"  # set default server

      # access to credentials configuration ...
      cc.set_site_config("https://foo.bar/ows", username="...", password="...")
      cc.set_site_config("https://foo2.bar/ows", token="...")

      cc.save()    # save configuration

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
            # make the saved file private
            if os.name == 'posix':
                os.chmod(file_.fileno(), 0o0600)

    def __str__(self):
        """ Dump configuration to a string. """
        fobj = StringIO()
        self._config.write(fobj)
        return fobj.getvalue()


    def init(self, env_var_name="VIRES_ACCESS_CONFIG"):
        """ Initialize client configuration. """
        env_config = _parse_env_config(_get_env_config(env_var_name))

        if not self.default_url:
            url = _get_ows_url(env_config['default_server'])
            print("Setting default URL to %s ..." % url)
            self.default_url = url

        # retrieve and server tokens
        for server_url, token_dict in env_config['servers'].items():
            url = _get_ows_url(server_url)
            if self.get_site_config(url):
                continue
            print("Creating new access token for %s ..." % url)
            try:
                token = _retrieve_access_token(
                    server_url, token_dict['token'], env_config["instance_name"]
                )
            except TokenManager.Error as error:
                print("ERROR: Failed to create a new access token! Reason: %s" % error)
                continue
            self.set_site_config(url, token=token)


def _retrieve_access_token(url, token, purpose):
    return TokenManager(url, token).post(purpose=purpose)['token']


def _get_env_config(env_var_name):
    return json.loads(os.environ[env_var_name])


def _parse_env_config(env_config):
    return {
        "instance_name": env_config.get("instance_name") or DEFAULT_SERVER,
        "default_server": env_config.get("default_server") or DEFAULT_SERVER,
        "servers": env_config.get("servers") or {},
    }
