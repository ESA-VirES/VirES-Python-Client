#-------------------------------------------------------------------------------
#
# Handles the WPS requests to the VirES server
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


from os.path import isfile#, join, dirname
from .wps.wps_vires import ViresWPS10Service
# from .wps.time_util import parse_datetime
from .wps.http_util import encode_basic_auth
from logging import getLogger, DEBUG
from .wps.log_util import set_stream_handler
# from jinja2 import Environment, FileSystemLoader
from .wps.environment import JINJA2_ENVIRONMENT
# import json


class ReturnedData:
    """Holds the data returned from the server and the data type.
    Provides output to different file types.
    """

    def __init__(self,data=bytes(),filetype=str()):
        self.data = data
        self.filetype = filetype

    def __str__(self):
        return "viresclient ReturnedData object of type " + self.filetype + \
            "\nSave it to a file with .to_file('filename')"

    def data():
        doc = "The data property."
        def fget(self):
            return self._data
        def fset(self, value):
            try:
                assert isinstance(value,bytes)
            except AssertionError as e:
                e.args += ("data must be of type bytes",)
                raise
            self._data = value
        def fdel(self):
            del self._data
        return locals()
    data = property(**data())

    def filetype():
        doc = "The filetype property."
        def fget(self):
            return self._filetype
        def fset(self, value):
            try:
                value = value.lower()
                assert value in ("csv","cdf")
            except AttributeError as e:
                e.args += ("filetype must be a string",)
                raise
            except AssertionError as e:
                e.args += ("Chosen filetype must be one of: 'csv', 'cdf'",)
                raise
            self._filetype = value
        def fdel(self):
            del self._filetype
        return locals()
    filetype = property(**filetype())

    def to_file(self,filename,overwrite=False):
        """Saves the data to the specified file.
        Only write to file if it does not yet exist, or if overwrite=True
        """
        try:
            assert isinstance(filename,str)
        except AssertionError as e:
            e.args += ("filename must be a string",)
            raise
        if not isfile(filename) or overwrite:
            with open(filename, 'wb') as f:
                f.write(self.data)
            print("Data written to",filename)
        else:
            print("File not written as it already exists and overwrite=False")


class ClientRequest:
    """Handles the requests to the server.
    """

    def __init__(self,url,username,password):

        try:
            assert isinstance(url,str)
            assert isinstance(username,str)
            assert isinstance(password,str)
        except AssertionError as e:
            e.args += ("url, username, and password must all be strings",)
            raise

        self.spacecraft = ''
        self.collections = []
        self.models = []
        self.variables = []
        self.filters = []

        # setting up console logging (optional)
        self._logger = getLogger()
        set_stream_handler(self._logger, DEBUG)
        self._logger.debug("TEST LOG MESSAGE")

        # service proxy with basic HTTP authentication
        self._wps = ViresWPS10Service(
            url,
            encode_basic_auth(username, password),
            logger=self._logger
        )

        # TODO: connect to the server and get a list of available products

    def set_collections(self,spacecraft, collections):
        self.spacecraft = spacecraft
        self.collections = collections

    def set_products(self,measurements, models, auxiliaries):
        self.measurements = measurements
        self.models = models
        self.auxiliaries = auxiliaries
        # Set up the variables that actually get passed to the WPS request
        variables = []
        variables += self.measurements
        variables += self.auxiliaries
        # Model values
        for model_name in self.models:
            for measurement in self.measurements:
                variables += ["%s_%s"%(measurement,model_name)]
        # Model residuals
        for model_name in self.models:
            for measurement in self.measurements:
                variables += ["%s_res_%s"%(measurement,model_name)]
        self.variables = variables

    def set_range_filter(self,parameter, minimum, maximum):
        self.filters = parameter+":"+str(minimum)+","+str(maximum)

    def get_between(self,start_time,end_time,filetype="csv",async=True):
        self.start_time = start_time
        self.end_time = end_time

        try:
            assert async in [True,False]
        except AssertionError as e:
            e.args += ("async must be set to either True or False",)
            raise

        retdata = ReturnedData(filetype=filetype)
        self.filetype = retdata.filetype

        if self.filetype == "csv":
            self.response_type = "text/csv"
        elif self.filetype == "cdf":
            self.response_type = "application/x-cdf"

        if async:
            # asynchronous WPS request
            templatefile = "test_vires_fetch_filtered_data_async.xml"
        else:
            # synchronous WPS request
            templatefile = "test_vires_fetch_filtered_data.xml"
        self.template = JINJA2_ENVIRONMENT.get_template(
            templatefile
        )

        self.request = self.template.render(
            begin_time=self.start_time,
            end_time=self.end_time,
            model_ids=self.models,
            variables=self.variables,
            collection_ids={self.spacecraft: self.collections},
            filters = self.filters,
            response_type=self.response_type,
        ).encode('UTF-8')

        if async:
            response = self._wps.retrieve_async(self.request)
        else:
            response = self._wps.retrieve(self.request)

        retdata.data = response
        return retdata
