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


import datetime
import json
from tqdm import tqdm
from os import path, mkdir
from datetime import datetime
import shutil

from ._wps.wps_vires import ViresWPS10Service
# from .wps.time_util import parse_datetime
from ._wps.http_util import encode_basic_auth
from logging import getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
from ._wps.log_util import set_stream_handler
# from jinja2 import Environment, FileSystemLoader
from ._wps.environment import JINJA2_ENVIRONMENT
from ._wps import time_util
from ._wps.wps import WPSError

from viresclient import VIRESCLIENT_DEFAULT_FILE_DIR
from ._data_handling import ReturnedDataInMemory, ReturnedDataOnDisk

LEVELS = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR,
    "NO_LOGGING": CRITICAL + 1,
}


def get_log_level(level):
    if isinstance(level, str):
        return LEVELS[level]
    else:
        return level


def wps_xml_request(templatefile, inputs):
    """Creates a WPS request object that can later be executed

    Args:
     templatefile (str): Name of the xml template file
     input (WPSInputs): Contains valid parameters to fill the template
    """
    if not isinstance(inputs, WPSInputs):
        raise TypeError("inputs must be a WPSInputs object")
    template = JINJA2_ENVIRONMENT.get_template(templatefile)
    request = template.render(**inputs.as_dict).encode('UTF-8')
    return request


class WPSInputs(object):
    """Holds the set of inputs to be passed to the request template

    Properties of this class are the set of valid inputs to a WPS request.
    See SwarmWPSInputs and AeolusWPSInputs.
    Also contains an as_dict property which converts its contents to a
    dictionary to be passed as kwargs to wps_xml_request() which fills the xml
    template.
    """

    def __init__(self):
        self.names = ()

    def __str__(self):
        if len(self.names) == 0:
            return None
        else:
            return "Request details:\n{}".format('\n'.join(
                ['{}: {}'.format(key, value) for (key, value) in
                 self.as_dict.items()
                 ]))

    @property
    def as_dict(self):
        return {key: self.__dict__['_{}'.format(key)] for key in self.names}


class ProgressBar(object):
    """Generates a progress bar from the WPS status.
    """

    def __init__(self):
        self.percentCompleted = 0
        self.lastpercent = 0

        l_bar = 'Processing: {percentage:3.0f}%|'
        bar = '{bar}'
        r_bar = '|  [ Elapsed: {elapsed}, Remaining: {remaining} {postfix}]'
        bar_format = '{}{}{}'.format(l_bar, bar, r_bar)
        self.tqdm_pbar = tqdm(total=100, bar_format=bar_format)

        self.refresh_tqdm()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    def cleanup(self):
        self.tqdm_pbar.close()

    def update(self, wpsstatus):
        """Updates the internal state based on the state of a WPSStatus object.
        """
        self.lastpercent = self.percentCompleted
        self.percentCompleted = wpsstatus.percentCompleted
        if self.lastpercent != self.percentCompleted:
            self.refresh_tqdm()

    def refresh_tqdm(self):
        """Updates the output of the progress bar.
        """
        if self.percentCompleted is None:
            return
        self.tqdm_pbar.update(self.percentCompleted-self.lastpercent)
        if self.percentCompleted == 100:
            self.cleanup()
            print('Downloading...')


class ClientRequest(object):
    """Handles the requests to and downloads from the server.

    See SwarmClientRequest and AeolusClientRequest
    """

    def __init__(self, url=None, username=None, password=None,
                 logging_level="NO_LOGGING", server_type="Swarm",
                 files_dir=VIRESCLIENT_DEFAULT_FILE_DIR
                 ):

        for i in [url, username, password]:
            if not isinstance(i, str):
                raise TypeError(
                    "url, username, and password must all be strings"
                )

        self._server_type = server_type
        self._request_inputs = None
        self._templatefiles = None
        self._supported_filetypes = None

        logging_level = get_log_level(logging_level)
        self._logger = getLogger()
        set_stream_handler(self._logger, logging_level)

        # service proxy with basic HTTP authentication
        self._wps_service = ViresWPS10Service(
            url,
            encode_basic_auth(username, password),
            logger=self._logger
        )

        self.files_dir = files_dir
        if not path.exists(self.files_dir):
            mkdir(self.files_dir)
        self._logger.info(
            "Set directory for saving files locally: ".format(self.files_dir)
        )

    def __str__(self):
        if self._request_inputs is None:
            return "No request set"
        else:
            return self._request_inputs.__str__()

    def get_between(self, start_time, end_time,
                    filetype="csv", asynchronous=True, on_disk=False):
        """Make the server request and download the data.

        Args:
            start_time (datetime)
            end_time (datetime)
            filetype (str): one of ('csv', 'cdf')
            asynchronous (bool): True for asynchronous processing,
                False for synchronous
            on_disk (bool): If True, save file directly on disk
                instead of holding in memory

        Returns:
            ReturnedData object

        """

        if asynchronous not in [True, False]:
            raise TypeError("asynchronous must be set to either True or False")

        # Initialise the ReturnedData so that filetype checking is done there
        if on_disk:
            retdata = ReturnedDataOnDisk(filetype=filetype)
        else:
            retdata = ReturnedDataInMemory(filetype=filetype)

        if retdata.filetype not in self._supported_filetypes:
            raise TypeError("filetype: {} not supported by server"
                            .format(filetype)
                            )
        if retdata.filetype == "csv":
            response_type = "text/csv"
        elif retdata.filetype == "cdf":
            response_type = "application/x-cdf"
        elif retdata.filetype == "netcdf":
            response_type = "application/netcdf"

        if asynchronous:
            # asynchronous WPS request
            templatefile = self._templatefiles['async']
        else:
            # synchronous WPS request
            templatefile = self._templatefiles['sync']

        # Finalise the WPSInputs object
        self._request_inputs.begin_time = start_time
        self._request_inputs.end_time = end_time
        self._request_inputs.response_type = response_type

        self._request = wps_xml_request(templatefile, self._request_inputs)

        if on_disk:
            # Save to a file named with the current time
            file_name = '.'.join([
                datetime.now().strftime('%Y%m%d%H%M%S'),
                retdata.filetype
                ])
            self.file_path = path.join(self.files_dir, file_name)
            if path.exists(self.file_path):
                raise Exception('File exists already')

            def write_response_to_disk(file_obj):
                """Acts on a file object to copy it to a file
                https://stackoverflow.com/a/7244263
                """
                with open(self.file_path, 'wb') as out_file:
                    shutil.copyfileobj(file_obj, out_file)

            response_handler = write_response_to_disk

        else:
            response_handler = None

        try:
            if asynchronous:
                with ProgressBar() as progressbar:
                    response = self._wps_service.retrieve_async(
                        self._request,
                        handler=response_handler,
                        status_handler=progressbar.update
                    )
            else:
                response = self._wps_service.retrieve(
                    self._request,
                    handler=response_handler
                )
        except WPSError:
            raise RuntimeError(
                "Server error - may be outside of product availability?"
                )

        if on_disk:
            retdata.data_path = self.file_path
        else:
            retdata.data = response
        return retdata
