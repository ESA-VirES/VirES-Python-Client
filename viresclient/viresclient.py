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


from os.path import join, dirname
from .wps.wps_vires import ViresWPS10Service
from .wps.time_util import parse_datetime
from .wps.http_util import encode_basic_auth
from logging import getLogger, DEBUG
from .wps.log_util import set_stream_handler
from jinja2 import Environment, FileSystemLoader
from .wps.environment import JINJA2_ENVIRONMENT
import json


class ClientRequest:

    def __init__(self,url,username,password,async=True):

        self.async = async

        # setting up console logging (optional)
        self.logger = getLogger()
        set_stream_handler(self.logger, DEBUG)
        self.logger.debug("TEST LOG MESSAGE")

        # service proxy with basic HTTP authentication
        self.wps = ViresWPS10Service(
            url,
            encode_basic_auth(username, password),
            logger=self.logger
        )

        if async:
            # asynchronous WPS request
            self.template = JINJA2_ENVIRONMENT.get_template(
                "test_vires_fetch_filtered_data_async.xml"
            )
        else:
            # synchronous WPS request
            self.template = JINJA2_ENVIRONMENT.get_template(
                "test_vires_fetch_filtered_data.xml"
            )

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

    def get_between(self,start_time,end_time):
        self.start_time = parse_datetime(start_time)
        self.end_time = parse_datetime(end_time)

        self.request = self.template.render(
            begin_time=self.start_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={self.spacecraft: self.collections},
            filters = self.filters,
            response_type="text/csv",
        ).encode('UTF-8')

        if self.async:
            response = self.wps.retrieve_async(self.request)
        else:
            response = self.wps.retrieve(self.request)

        return response
        # output = {}
        # for key in response.keys():
        #     output[key] = array(response[key])
        #
        # return output
