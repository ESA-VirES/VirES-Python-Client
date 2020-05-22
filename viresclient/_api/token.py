#-------------------------------------------------------------------------------
#
# vires API - token management API proxy
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

import re
import requests
from .._wps.http_util import encode_token_auth


class TokenManager():
    """ VirES for Swarm token management API proxy.

    Example usage::

      from pprint import pprint
      from viresclient import TokenManager

      tm = TokenManager("https://vires.services", token="...")

      # create a new token
      token_info = tm.post(purpose="Test token.", expires="PT2H")

      pprint(token_info)
      {'created': '2020-05-18T20:26:07.414846+00:00',
       'expires': '2020-05-18T22:26:07.414401+00:00',
       'identifier': '...',
       'purpose': 'Test token.',
       'token': '...'}

    """
    RE_URL_BASE = re.compile(r"(/(ows)?)?$")
    PATH_TOKEN_API = "/accounts/api/tokens/"

    class Error(Exception):
        """ Token manager error exception. """

    def __init__(self, url, token):
        self.url = self.get_api_url(url)
        self.token = token
        self.headers = encode_token_auth(token=token)

    def post(self, purpose=None, expires=None):
        """ HTTP POST
        Create a new token.
        Accepted parameters:
          purpose   optional text label describing purpose of the token
          expires   optional token expiration as ISO timestamp or ISO duration
        """
        response = requests.post(self.url, headers=self.headers, json={
            "purpose": purpose,
            "expires": expires,
        })

        if response.status_code != 200:
            raise self.Error("%s %s: %s" % (
                response.status_code, response.reason, response.text
            ))

        return response.json()

    @classmethod
    def get_api_url(cls, url):
        """ Translate WPS URL path to the upload REST/API URL path. """
        return cls.RE_URL_BASE.sub(cls.PATH_TOKEN_API, url, count=1)
