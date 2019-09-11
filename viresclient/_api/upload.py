#-------------------------------------------------------------------------------
#
# vires API - data upload API proxy
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

import json
from os.path import basename
import requests
from .._wps.http_util import encode_token_auth


class DataUpload():
    """ VirES for Swarm data upload API proxy.

    Example usage::

      from viresclient import ClientConfig, DataUpload

      du = DataUpload("https://vires.services", token="...")

      cc = ClientConfig()
      url = cc.default_url
      du = DataUpload(url, **cc.get_site_config(url))

      # upload file
      info = du.post("example.csv")
      print(info)

      # get information about the uploaded files
      info = du.get()
      print(info)

      # remove any uploaded files
      du.clear()

      # check if the upload is valid and get list of missing mandatory parameters
      info = du.post("example.cdf")
      is_valid = info.get('is_valid', True)
      missing_fields = info.get('missing_fields', {}).keys()
      print(is_valid, missing_fields)

      # get constant parameters
      id = info['identifier']
      parameters = du.get_constant_parameters(id)
      print(parameters)

      # set new constant parameters
      parameters = du.set_constant_parameters(id, {'Radius': 7000000, 'Latitude': 24.0})
      print(parameters)

      # clear all constant parameters
      parameters = du.set_constant_parameters(id, {}, replace=True)
      print(parameters)

    For more information about the supported file format see the
    `file format specification <https://github.com/ESA-VirES/VirES-Server/blob/master/vires/custom_data_format_description.md>`_

    """
    PATH_OWS = "/ows"
    PATH_UPLOAD = "/custom_data/"

    class Error(Exception):
        """ Data upload error exception. """

    def __init__(self, url, token, **kwargs):
        self.url = self.get_api_url(url) # translates path from /ows to /custom_data/
        self.token = token
        self.headers = encode_token_auth(token=token)

    @property
    def ids(self):
        """ Get list of identifiers. """
        return [item['identifier'] for item in self.get()]

    def clear(self):
        """ Remove all uploaded items.  """
        for id_ in self.ids:
            self.delete(id_)

    def post(self, file, filename=None):
        """ HTTP POST multipart/form-data
        Upload file to the server and get info about the uploaded file.
        """
        def _post(file, filename):
            return requests.post(self.url, headers=self.headers, files={
                "file": (filename, file),
            })

        if isinstance(file, str):
            if not filename:
                filename = basename(file)
            with open(file, "rb") as fobj:
                response = _post(fobj, filename)
        else:
            response = _post(file, filename)

        if response.status_code != 200:
            raise self.Error("%s %s: %s" % (
                response.status_code, response.reason, response.text
            ))

        return json.loads(response.text)


    def get_constant_parameters(self, identifier):
        """ Get dictionary of the currently set constant parameters. """
        return self._extract_constant_values(self.get(identifier))

    def set_constant_parameters(self, identifier, parameters, replace=False):
        """ Set constant parameters form from give key value dictionary.
        Set replace to True if you prefer to replace the already set parameters
        rather then update them.
        """
        if replace:
            parameters_all = parameters
        else:
            parameters_all = self.get_constant_parameters(identifier)
            parameters_all.update(parameters)

        return self._extract_constant_values(self.patch(identifier, {
            "constant_fields": {
                name: {"value": value} for name, value in parameters_all.items()
            }
        }))

    def patch(self, identifier, data):
        """ REST/API PATCH
        Update metadata of the uploaded dataset.
        """
        url = self.url + (identifier or "")
        headers = {'Content-Type': 'application/json'}
        headers.update(self.headers)
        response = requests.patch(url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            raise self.Error("%s %s: %s" % (
                response.status_code, response.reason, response.text
            ))
        return json.loads(response.text)

    def get(self, identifier=None):
        """ REST/API GET
        If an identifier provided, get info about the uploaded item.
        If no identifier provided, list all uploaded items.
        """
        url = self.url + (identifier or "")
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise self.Error("%s %s: %s" % (
                response.status_code, response.reason, response.text
            ))
        return json.loads(response.text)

    def delete(self, identifier):
        """ REST/API DELETE request.
        Delete item of the given identifier.
        """
        url = self.url + identifier
        response = requests.delete(url, headers=self.headers)
        if response.status_code != 204:
            raise self.Error("%s %s: %s" % (
                response.status_code, response.reason, response.text
            ))

    @classmethod
    def get_api_url(cls, url):
        """ Translate WPS URL path to the upload REST/API URL path. """
        return cls._replace_path(url, cls.PATH_OWS, cls.PATH_UPLOAD) or url

    @classmethod
    def get_ows_url(cls, url):
        """ Translate REST/API URL path to the upload WPS URL path. """
        return (
            cls._replace_path(url, cls.PATH_UPLOAD, cls.PATH_OWS) or
            cls._replace_path(url, cls.PATH_UPLOAD[:-1], cls.PATH_OWS)
            or url
        )

    @staticmethod
    def _replace_path(url, path_old, path_new):
        if path_old and url.endswith(path_old):
            return url[:-len(path_old)] + path_new
        return None

    @staticmethod
    def _extract_constant_values(data):
        return {
            name: info['value'] for name, info
            in data.get('constant_fields', {}).items()
        }
