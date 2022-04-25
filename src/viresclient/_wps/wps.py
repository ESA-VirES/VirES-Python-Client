#-------------------------------------------------------------------------------
#
# WPS 1.0 service proxy
#
# Authors: Martin Paces <martin.paces@eox.at>
#          Ashley Smith <ashley.smith@ed.ac.uk>
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

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    # Python 2 backward compatibility
    from urllib2 import urlopen, Request, HTTPError

from time import sleep
from logging import getLogger, LoggerAdapter
from contextlib import closing
from xml.etree import ElementTree
from .time_util import Timer

NS_OWS11 = "http://www.opengis.net/ows/1.1"
NS_OWS20 = "http://www.opengis.net/ows/2.0"


class WPSStatus(object):
    """ WPS status information.
    Matches output from WPS10Service.poll_status()
    """
    def __init__(self):
        self.status = None
        self.percentCompleted = 0
        self.url = None
        self.execute_response = None

    def update(self, status, percentCompleted, url, execute_response):
        self.status = status
        self.percentCompleted = percentCompleted
        self.url = url
        self.execute_response = execute_response


class WPSError(Exception):
    """ WPS error exception """
    def __init__(self, code, locator, text):
        self.ows_exception_code = code
        self.ows_exception_text = code
        self.ows_exception_locator = locator
        Exception.__init__(self, "WPS Request Failed! Reason: %s%s%s" % (
            code or "", " [%s]" % locator if locator else "",
            ": %s" % text if text else ""
        ))


class AuthenticationError(Exception):
    """ Authentication error exception """
    def __init__(self, text=None):
        Exception.__init__(
            self, "Perhaps credentials are missing or invalid. {}"
            .format(text if text else ""))


class WPS10Service(object):
    """ WPS 1.0 service proxy class.

        wps = WPS10Service(url, headers)

        Parameters:
            url     - service URL
            headers - optional dictionary of the HTTP headers sent with each
                      request
    """
    STATUS = {
        "{http://www.opengis.net/wps/1.0.0}ProcessAccepted": "ACCEPTED",
        "{http://www.opengis.net/wps/1.0.0}ProcessFailed": "FAILED",
        "{http://www.opengis.net/wps/1.0.0}ProcessStarted": "STARTED",
        "{http://www.opengis.net/wps/1.0.0}ProcessSucceeded": "FINISHED",
    }

    class _LoggerAdapter(LoggerAdapter):
        def process(self, msg, kwargs):
            return 'WPS10Service: %s' % msg, kwargs

    def __init__(self, url, headers=None, logger=None):
        self.url = url
        self.headers = headers or {}
        self.logger = self._LoggerAdapter(logger or getLogger(__name__), {})

    def retrieve(self, request, handler=None):
        """ Send a synchronous POST WPS request to a server and retrieve
        the output.
        """
        return self._retrieve(
            Request(self.url, request, self.headers),
            handler, self.error_handler
        )

    def retrieve_async(self, request, handler=None, status_handler=None,
                       cleanup_handler=None, polling_interval=1,
                       output_name="output"):
        """ Send an asynchronous POST WPS request to a server and retrieve
        the output.
        """
        timer = Timer()
        status, percentCompleted, status_url, execute_response = self.submit_async(request)
        wpsstatus = WPSStatus()
        wpsstatus.update(status, percentCompleted, status_url, execute_response)

        def log_wpsstatus(wpsstatus):
            self.logger.info(
                "%s %s %.3fs",
                wpsstatus.status, wpsstatus.url, timer.elapsed_time
                )

        def log_wpsstatus_percentCompleted(wpsstatus):
            self.logger.info(
                "{:.3f}s elapsed: Percent Completed: {}\n".format(
                    timer.elapsed_time, wpsstatus.percentCompleted)
            )

        try:
            log_wpsstatus(wpsstatus)
            if status_handler:
                status_handler(wpsstatus)

            while wpsstatus.status not in ("FINISHED", "FAILED"):
                sleep(polling_interval)

                last_status = wpsstatus.status
                last_percentCompleted = wpsstatus.percentCompleted
                wpsstatus.update(*self.poll_status(wpsstatus.url))

                if wpsstatus.status != last_status:
                    log_wpsstatus(wpsstatus)
                if wpsstatus.percentCompleted != last_percentCompleted:
                    log_wpsstatus_percentCompleted(wpsstatus)
                if status_handler:
                    status_handler(wpsstatus)

            if wpsstatus.status == "FAILED":
                ows_exception, namespace = self.find_exception(wpsstatus.execute_response)
                raise self.parse_ows_exception(ows_exception, namespace)

            output = self.retrieve_async_output(
                wpsstatus.execute_response, output_name, handler
            )

        finally:
            (cleanup_handler or self._default_cleanup_handler)(status_url)

        return output

    def retrieve_async_output(self, status_url, output_name, handler=None):
        """ Retrieve asynchronous job output reference. """
        self.logger.debug(
            "Retrieving asynchronous job output '%s'.", output_name
        )
        output_url = self.parse_output_reference(status_url, output_name)
        return self._retrieve(Request(output_url, None, self.headers), handler)

    @staticmethod
    def parse_output_reference(xml, identifier):
        """ Parse output reference. """
        root = xml.getroot()
        wps_outputs = root.find("{http://www.opengis.net/wps/1.0.0}ProcessOutputs")
        for elm in wps_outputs.findall("./{http://www.opengis.net/wps/1.0.0}Output"):
            elm_id = elm.find("./{http://www.opengis.net/ows/1.1}Identifier")
            if elm_id is not None and identifier == elm_id.text:
                elm_reference = elm.find(
                    "./{http://www.opengis.net/wps/1.0.0}Reference"
                )
                return elm_reference.attrib["href"]


    def submit_async(self, request):
        """ Send a POST WPS asynchronous request to a server and retrieve
        the status URL.
        """
        self.logger.debug("Submitting asynchronous job.")
        return self._retrieve(
            Request(self.url, request, self.headers),
            self.parse_status, self.error_handler
        )

    def poll_status(self, status_url):
        """ Poll status of an asynchronous WPS job. """
        self.logger.debug("Polling asynchronous job status.")
        return self._retrieve(
            Request(status_url, None, self.headers), self.parse_status
        )

    @classmethod
    def parse_status(cls, response):
        """ Parse process status and status location. """
        xml = ElementTree.parse(response)
        return (
            cls.parse_process_status(xml),
            cls.parse_process_percentCompleted(xml),
            cls.parse_status_location(xml),
            xml
        )

    @staticmethod
    def parse_status_location(xml):
        """ Parse status location from an asynchronous WPS execute response. """
        return xml.getroot().attrib["statusLocation"]

    @classmethod
    def parse_process_status(cls, xml):
        """ Parse status from an asynchronous WPS execute response. """
        root = xml.getroot()
        elm_status = root.find("{http://www.opengis.net/wps/1.0.0}Status")
        if elm_status is None:
            # status not found
            return None
        for elm in elm_status:
            return cls.STATUS[elm.tag]

    @classmethod
    def parse_process_percentCompleted(cls, xml):
        """ Parse percentCompleted from an asynchronous WPS execute response. """
        root = xml.getroot()
        elm_status = root.find("{http://www.opengis.net/wps/1.0.0}Status")
        if elm_status is None:
            # status not found
            return None
        for elm in elm_status:
            if cls.STATUS[elm.tag] == "ACCEPTED":
                return 0
            elif cls.STATUS[elm.tag] == "STARTED":
                # if "percentCompleted" in elm.attrib.keys():
                return int(elm.attrib["percentCompleted"])
            elif cls.STATUS[elm.tag] == "FINISHED":
                return 100
            else:
                return None

    @classmethod
    def error_handler(cls, http_error):
        """ Handle HTTP error and parse OWS exception. """
        if http_error.status in [401, 403]:
            raise AuthenticationError
        try:
            xml = ElementTree.parse(http_error)
            ows_exception, namespace = cls.find_exception(xml)
        except ElementTree.ParseError:
            raise http_error
        raise cls.parse_ows_exception(ows_exception, namespace)

    @classmethod
    def parse_ows_exception(cls, ows_exception, namespace):
        """ Parse OWS exception. """
        locator = ows_exception.attrib.get("locator")
        code = ows_exception.attrib.get("exceptionCode")
        text_element = ows_exception.find("{%s}ExceptionText" % namespace)
        text = None if text_element is None else text_element.text
        return WPSError(code, locator, text)

    @classmethod
    def find_exception(cls, xml):
        """ Find OWS exception element in the given XML document. """
        element = xml.getroot()
        for namespace in (NS_OWS11, NS_OWS20):
            ows_exception = element.find(".//{%s}Exception" % namespace)
            if ows_exception is not None:
                return ows_exception, namespace
        else:
            raise ElementTree.ParseError

    def _retrieve(self, request, response_handler=None, error_handler=None):
        """ Retrieve and parse HTTP response. """
        method = request.get_method()
        url = request.get_full_url()
        timer = Timer()
        try:
            with closing(urlopen(request)) as file_in:
                output = (response_handler or self._default_handler)(file_in)
            self.logger.info(
                "%d %s %s %.3fs", 200, method, url, timer.elapsed_time
            )
            return output
        except HTTPError as error:
            self.logger.error(
                "%d %s %s %.3fs", error.code, method, url, timer.elapsed_time
            )
            if error_handler:
                return error_handler(error)
            raise

    def _default_cleanup_handler(self, status_url):
        pass

    @staticmethod
    def _default_handler(file_obj):
        return file_obj.read()
