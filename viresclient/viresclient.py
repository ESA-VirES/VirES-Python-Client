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


from datetime import timedelta
from numpy import array

from .wps_util import (
    WpsPostRequestMixIn, WpsAsyncPostRequestMixIn, CsvRequestMixIn,
)
from .time_util import parse_datetime


# START_TIME = parse_datetime("2016-01-01T00:00:00Z")
# END_TIME = START_TIME + timedelta(days=1)


class AsyncFetchFilteredDataMixIn(CsvRequestMixIn, WpsAsyncPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"
    # begin_time = START_TIME
    # end_time = END_TIME


class GetMeasurementsAndModel(object):

    @property
    def variables(self):
#         return ["F_%s"%self.model_name, "B_NEC_%s"%self.model_name]
#         return ["%s_%s"%(self.measurement,self.model_name)]
        variables = []
        for model_name in self.models:
            for measurement in self.measurements:
                variables += ["%s_%s"%(measurement,model_name)]
        return variables

    @property
    def residual_variables(self):
#         return ["F_res_%s"%self.model_name, "B_NEC_res_%s"%self.model_name]
#         return ["%s_res_%s"%(self.measurement,self.model_name)]
        residual_variables = []
        for model_name in self.models:
            for measurement in self.measurements:
                residual_variables += ["%s_res_%s"%(measurement,model_name)]
        return residual_variables

    @property
    def measurements_variables(self):
#         return ["F", "B_NEC", "OrbitNumber", "Kp", "IMF_BZ_GSM"]
        return self.measurements + self.auxiliaries

    def get_measurements(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            model_ids=[model_name for model_name in self.models],
            variables=(
                self.measurements_variables +
                #self.residual_variables +
                self.variables
            ),
            filters = self.filters,
            collection_ids={self.spacecraft: self.collections},
        )
        response = self.get_parsed_response(request)

#         measurement_f = array(response["F"])
#         measurement_b = array(response["B_NEC"])
#         model_f = array(response["F_%s" % self.model_name])
#         model_b = array(response["B_NEC_%s" % self.model_name])
#         diff_f = array(response["F_res_%s" % self.model_name])
#         diff_b = array(response["B_NEC_res_%s" % self.model_name])
#         orbno = array(response["OrbitNumber"])
#         Kp = array(response["Kp"])
#         IMF_BZ_GSM = array([response["IMF_BZ_GSM"]])

#         measurement = array(response[self.measurement])
#         model = array(response[self.residual_variables])

#         output = dict.fromkeys(response.keys())
        output = {}
        for key in response.keys():
            output[key] = array(response[key])

        return output
#         return {"F":measurement_f, "B_NEC":measurement_b,
#                 "F_%s" % self.model_name:model_f, "B_NEC_%s" % self.model_name:model_b,
#                 "OrbitNumber":orbno, "Kp":Kp, "IMF_BZ_GSM":IMF_BZ_GSM}


class AsyncFetchMeasurementsAndModel(GetMeasurementsAndModel, AsyncFetchFilteredDataMixIn):
    pass
#     model_name = "CHAOS-6-Combined"
#     filters = "SunZenithAngle:0,90"
#     begin_time = parse_datetime("2016-01-01T00:00:00Z")
#     end_time = begin_time + timedelta(hours=1)


class ClientRequest(AsyncFetchMeasurementsAndModel):

    def __init__(self,url,username,password):
        self.service_url = url
        # NOT YET IMPLEMENTED

#     def query_avail_collections():

    def set_collections(self,spacecraft, collections):
        self.spacecraft = spacecraft
        self.collections = collections

#     def query_avail_products:

    def set_products(self,measurements, models, auxiliaries):
        self.measurements = measurements
        self.models = models
        self.auxiliaries = auxiliaries

    def set_range_filter(self,parameter, minimum, maximum):
        self.filters = parameter+":"+str(minimum)+","+str(maximum)

    def get_between(self,start_time,end_time):
        self.begin_time = start_time
        self.end_time = end_time

        return self.get_measurements()
