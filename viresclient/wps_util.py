#-------------------------------------------------------------------------------
#
# VirES integration tests - WPS utilities
#
# Author: Martin Paces <martin.paces@eox.at>
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
# pylint: disable=missing-docstring

from time import sleep
import xml.etree.ElementTree as ElementTree
import json
# from string import maketrans
from contextlib import closing
# from urllib2 import urlopen, Request, HTTPError
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from jinja2 import Environment, FileSystemLoader
from time_util import parse_datetime

# SERVICE_URL = "http://127.0.0.1:8300/ows"
SERVICE_URL = "https://staging.viresdisc.vires.services/openows"

JINJA2_ENVIRONMENT = Environment(loader=FileSystemLoader("./templates"))
JINJA2_ENVIRONMENT.filters.update(
    d2s=lambda d: d.isoformat("T") + "Z",
    l2s=lambda l: ", ".join(str(v) for v in l),
    o2j=json.dumps,
)

WPS_STATUS = {
    "{http://www.opengis.net/wps/1.0.0}ProcessAccepted": "ACCEPTED",
    "{http://www.opengis.net/wps/1.0.0}ProcessFailed": "FAILED",
    "{http://www.opengis.net/wps/1.0.0}ProcessStarted": "STARTED",
    "{http://www.opengis.net/wps/1.0.0}ProcessSucceeded": "FINISHED",
}

def parse_array(value):
    return json.loads(
        value.translate(str.maketrans("{;}", "[,]")).replace("nan", "NaN")
    )


CSV_DEFAULT_TYPE = parse_array
CSV_VARIABLE_TYPES = {
    'id': str,
    'Spacecraft': str,
    #'UpwardCurrent': float,
    #'Timestamp': float,
    #'Latitude': float,
    #'Longitude': float,
    #'Radius': float,
    #'Kp': float,
    #'F': float,
    #'B_NEC': parse_array,
    #'B_VFM': parse_array,
    #'B_error': parse_array,
    #'F_error': float,
    #'Att_error': float,
    #'ASM_Freq_Dev': float,
    #'dF_AOCS': float,
    #'dB_AOCS': parse_array,
    #'dF_other': float,
    #'dB_other': parse_array,
    #'dB_Sun': parse_array,
    #'q_NEC_CRF': parse_array,
    #'SyncStatus': int,
    #'Flags_Platform': int,
    #'Flags_B': int,
    #'Flags_F': int,
    #'Flags_q': int,
    #'Dst': float,
    #'AscendingNodeTime': float,
    #'AscendingNodeLongitude': float,
    #'OrbitNumber': int,
    #'OrbitSource': int,
    #'SunDeclination': float,
    #'SunRightAscension': float,
    #'SunHourAngle': float,
    #'SunZenithAngle': float,
    #'SunAzimuthAngle': float,
    #'SunVector': parse_array,
    #'DipoleAxisVector': parse_array,
    #'DipoleTiltAngle': float,
    #'MLT': float,
    #'QDLat': float,
    #'QDLon': float,
    #'QDBasis': parse_array,
    #'F10_INDEX': float,
    #'IMF_BY_GSM': float,
    #'IMF_BZ_GSM': float,
    #'IMF_V': float,
}


class WpsException(Exception):
    def __init__(self, code, locator, text):
        Exception.__init__(
            self, "WPS Process Failed!\n%s [%s]: %s" % (code, locator, text)
        )


class HttpMixIn(object):
    url = SERVICE_URL
#     url = self.service_url

    @staticmethod
    def retrieve(request, parser):
        try:
            with closing(urlopen(request)) as file_in:
                return parser(file_in)
        except HTTPError as error:
            print(error.read())
            raise


class WpsPostRequestMixIn(HttpMixIn):
    url = SERVICE_URL
#     url = self.service_url
    headers = {"Content-Type": "application/xml"}
    template_source = None
    extra_template_params = {}

    @property
    def template(self):
        return self.get_template(self.template_source)

    @staticmethod
    def get_template(source):
        return JINJA2_ENVIRONMENT.get_template(source)

    def get_request(self, **template_params):
        template_params.update(self.extra_template_params)
        return self.template.render(**template_params).encode("UTF-8")

    def get_response(self, parser, request):
        return self.retrieve(Request(self.url, request, self.headers), parser)


class WpsAsyncPostRequestMixIn(WpsPostRequestMixIn):
    process_name = "vires:fetch_filtered_data_async"
    output_name = "output"
    template_list_jobs = "vires_list_jobs.xml"
    template_remove_job = "vires_remove_job.xml"
    extra_template_params = {"response_type": "text/csv"}

    def get_response(self, parser, request):
        execute_response = self.retrieve(
            Request(self.url, request, self.headers),
            ElementTree.parse
        )
        status_url = execute_response.getroot().attrib["statusLocation"]

        last_status = "none"
        print("Waiting on server...")
        while True:
            status = self.parse_process_status(execute_response)

            if status != last_status:
                print(status)
            last_status = status

            if status == "FINISHED":
                break

            if status == "FAILED":
                self.delete_all_async_jobs()
                self.raise_process_exception(execute_response)

            execute_response = self.retrieve(
                Request(status_url, None, self.headers),
                ElementTree.parse
            )
            status_url = execute_response.getroot().attrib["statusLocation"]
            sleep(1)
        print("Request complete. Loading file...")

        output_url = self.extract_output_reference(
            execute_response, self.output_name
        )

        response = self.retrieve(Request(output_url, None, self.headers), parser)
        self.delete_all_async_jobs()
        return response

    @staticmethod
    def extract_output_reference(xml, identifier):
        root = xml.getroot()
        wps_outputs = root.find("{http://www.opengis.net/wps/1.0.0}ProcessOutputs")
        for elm in wps_outputs.findall("./{http://www.opengis.net/wps/1.0.0}Output"):
            elm_id = elm.find("./{http://www.opengis.net/ows/1.1}Identifier")
            if elm_id is not None and identifier == elm_id.text:
                elm_reference = elm.find(
                    "./{http://www.opengis.net/wps/1.0.0}Reference"
                )
                return elm_reference.attrib["href"]

    @staticmethod
    def raise_process_exception(xml):
        elm_exception = xml.find(".//{http://www.opengis.net/ows/1.1}Exception")
        locator = elm_exception.attrib["locator"]
        exception_code = elm_exception.attrib["exceptionCode"]
        elm_exception_text = elm_exception.find(
            "{http://www.opengis.net/ows/1.1}ExceptionText"
        )
        exception_text = elm_exception_text.text
        raise WpsException(exception_code, locator, exception_text)

    @staticmethod
    def parse_process_status(xml):
        root = xml.getroot()
        elm_status = root.find("{http://www.opengis.net/wps/1.0.0}Status")
        if elm_status is None:
            # status not found
            return None

        for elm in elm_status:
            return WPS_STATUS[elm.tag]

    def delete_all_async_jobs(self):
        for item in self.list_async_jobs():
            if not self.remove_async_job(item["id"]):
                print("Failed to remove asynchronous job %s (%s)!" % (
                    item["id"], item["url"]
                ))

    def list_async_jobs(self):
        request = self.get_template(self.template_list_jobs).render().encode("UTF-8")
        job_list = self.retrieve(
            Request(self.url, request, self.headers),
            lambda r: json.loads(r.read().decode("UTF-8"))
        )
        return job_list.get(self.process_name, [])

    def remove_async_job(self, job_id):
        request = self.get_template(self.template_remove_job).render(
            job_id=job_id
        ).encode("UTF-8")
        return self.retrieve(
            Request(self.url, request, self.headers),
            lambda r: json.loads(r.read().decode("UTF-8"))
        )


class CsvRequestMixIn(object):
    extra_template_params = {"response_type": "text/csv"}

    @staticmethod
    def csv_parser(file_in):

        def wrap(parser):
            """ Wrap parser so that it catches exceptions and reports
            more details about the failed item.
            """
            def _wrap(variable, value):
                try:
                    return parser(value)
                except ValueError as exc:
                    raise ValueError(
                        "%s: %s\n%s" % (variable, value, exc)
                    )
            return _wrap

        def parse(source):
            header = next(source)
            types = [
                wrap(CSV_VARIABLE_TYPES.get(variable, CSV_DEFAULT_TYPE))
                for variable in header
            ]
            data = {variable: [] for variable in header}
            for record in source:
                for variable, value, type_ in zip(header, record, types):
                    data[variable].append(type_(variable, value))
            return data

        def split_records():
            for line in file_in:
                yield line.decode("UTF-8").rstrip().split(",")

        return parse(split_records())

    def get_parsed_response(self, request):
        return self.get_response(self.csv_parser, request)
