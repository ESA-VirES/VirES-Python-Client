# -------------------------------------------------------------------------------
#
# Handles the WPS requests to the VirES server
#
# Authors: Ashley Smith <ashley.smith@ed.ac.uk>
#          Martin Paces <martin.paces@eox.at>
#
# -------------------------------------------------------------------------------
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
# -------------------------------------------------------------------------------

import importlib
import json
import os
from datetime import timedelta
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, getLogger

# Identify whether code is running in Jupyter notebook or not
try:
    from IPython import get_ipython

    IN_JUPYTER = "zmqshell" in str(type(get_ipython()))
except Exception:
    IN_JUPYTER = False
# Only use the fancy HTML (notebook) progress bar when in compatible environment
if IN_JUPYTER and importlib.util.find_spec("ipywidgets") is not None:
    from tqdm.auto import tqdm
else:
    from tqdm import tqdm

from io import StringIO

from pandas import read_csv, to_datetime

from ._config import ClientConfig, set_token
from ._data_handling import ReturnedData

# from jinja2 import Environment, FileSystemLoader
from ._wps.environment import JINJA2_ENVIRONMENT
from ._wps.http_util import encode_basic_auth, encode_no_auth, encode_token_auth
from ._wps.log_util import set_stream_handler
from ._wps.time_util import parse_datetime, parse_duration
from ._wps.wps import AuthenticationError, WPSError
from ._wps.wps_vires import ViresWPS10Service

# Logging levels
LEVELS = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR,
    "NO_LOGGING": CRITICAL + 1,
}

DEFAULT_LOGGING_LEVEL = "ERROR"

# File type to WPS output name
RESPONSE_TYPES = {
    "csv": "text/csv",
    "cdf": "application/x-cdf",
    "nc": "application/netcdf",
}

# Maximum number of records allowable in one WPS request
NRECORDS_LIMIT = 4320000  # = 50 days at 1Hz

# Store the config file in home directory
CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".viresclient,ini")

# Maximum time-chunk size ~25 years
MAX_CHUNK_DURATION = timedelta(days=25 * 365.25)

TEMPLATE_FILES = {
    "list_jobs": "vires_list_jobs.xml",
    "getTimeData": "vires_getTimeData.xml",
}

AUTH_ERROR_TEXT = """
Invalid token? Set with viresclient.set_token().
For more details, see:
https://viresclient.readthedocs.io/en/latest/config_details.html"""

PRODUCTION_URLS = {
    "Swarm": "https://vires.services/ows",
    "Aeolus": "https://aeolus.services/ows",
}


def get_log_level(level):
    """Translate log-level string to an actual log level number accepted by
    the python logging."""
    if isinstance(level, str):
        level = LEVELS[level]
    return level


class WPSInputs:
    """Base WPS inputs class holding the set of inputs to be passed
    to the request template.

    Properties of this class are the set of valid inputs to a WPS request.
    See SwarmWPSInputs and AeolusWPSInputs.
    Also contains an as_dict property which converts its contents to a
    dictionary to be passed as kwargs to as_xml() which fills the xml
    template.
    """

    NAMES = []  # to be overridden in the sub-classes

    def __str__(self):
        return "Request details:\n{}".format(
            "\n".join([f"{key}: {value}" for (key, value) in self.as_dict.items()])
        )

    @property
    def as_dict(self):
        return {key: self.__dict__[f"_{key}"] for key in self.NAMES}

    def as_xml(self, templatefile):
        """Renders a WPS request template (xml) that can later be executed

        Args:
            templatefile (str): Name of the xml template file

        """
        template = JINJA2_ENVIRONMENT.get_template(templatefile)
        request = template.render(**self.as_dict).encode("UTF-8")
        return request


class ProgressBar:
    """Custom tqdm status bar"""

    def __init__(self, bar_format, total=100, leave=True):
        self.percentCompleted = 0
        self.lastpercent = 0
        self.tqdm_pbar = tqdm(
            total=total,
            bar_format=bar_format,
            leave=leave,
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    def cleanup(self):
        self.tqdm_pbar.close()

    def refresh_tqdm(self):
        """Updates the output of the progress bar."""
        if self.percentCompleted is None:
            return
        self.tqdm_pbar.update(self.percentCompleted - self.lastpercent)
        if self.percentCompleted == 100:
            self.cleanup()

    def write(self, message):
        """Command line output that doesn't interfere with the tqdm"""
        self.tqdm_pbar.write(message)


class ProgressBarChunks(ProgressBar):
    """A progress bar to track longer (chunked) requests"""

    def __init__(self, nchunks):
        l_bar = "{desc}"
        bar = "{bar}"
        r_bar = "|  [ Elapsed: {elapsed}, Remaining: {remaining}]  {postfix}"
        bar_format = f"{l_bar}{bar}{r_bar}"
        super().__init__(bar_format, total=nchunks + 1)

    def update(self, i, n, size, final=False):
        """Update the chunk iteration (i) and total file size"""
        # Update {desc} set above
        self.tqdm_pbar.set_description(f"Processing chunks [{i+1}/{n}]")
        size = round(size / 1e6, 3)
        filesize_display = f"({size} MB)" if final else f"(> {size} MB)"
        # Update {postfix} set above
        self.tqdm_pbar.set_postfix_str(filesize_display)
        # Update internal state of progress bar
        self.tqdm_pbar.update(1)


class ProgressBarProcessing(ProgressBar):
    """Generates a progress bar from the WPS status.

    Depends on ._wps.wps.WPSStatus
    """

    def __init__(self, extra_text=None, leave=True):
        extra_text = "" if extra_text is None else extra_text
        l_bar = "Processing:  {percentage:3.0f}%|"
        bar = "{bar}"
        r_bar = "|  [ Elapsed: {elapsed}, Remaining: {remaining} {postfix}]"
        bar_format = f"{l_bar}{bar}{r_bar} {extra_text}"
        super().__init__(bar_format, leave=leave)

    def update(self, wpsstatus):
        """Updates the internal state based on the state of a WPSStatus object."""
        self.lastpercent = self.percentCompleted
        self.percentCompleted = wpsstatus.percentCompleted
        if self.lastpercent != self.percentCompleted:
            self.refresh_tqdm()


class ProgressBarDownloading(ProgressBar):
    """Shows download progress and size,
    given a file size in bytes and updated with the percent completion
    """

    def __init__(self, size, leave=True):
        # Convert size to MB
        sizeMB = round(size / 1e6, 3)
        # if sizeMB > 1:
        #     sizeMB = round(sizeMB,)
        l_bar = "Downloading: {percentage:3.0f}%|"
        bar = "{bar}"
        r_bar = (
            "|  [ Elapsed: {{elapsed}}, "
            "Remaining: {{remaining}} {{postfix}}] "
            "({sizeMB}MB)".format(sizeMB=sizeMB)
        )
        bar_format = f"{l_bar}{bar}{r_bar}"
        super().__init__(bar_format, leave=leave)

    def update(self, percentCompleted):
        """Updates the internal state of the percentage completion."""
        self.lastpercent = self.percentCompleted
        self.percentCompleted = percentCompleted
        if self.lastpercent != self.percentCompleted:
            self.refresh_tqdm()


class ClientRequest:
    """Base class handling the requests to and downloads from the server."""

    def __init__(
        self,
        url=None,
        token=None,
        config=None,
        logging_level=DEFAULT_LOGGING_LEVEL,
        server_type=None,
    ):
        self._server_type = server_type

        # Check and prompt for token if not already set, then store in config
        # Try to only do this if running in a notebook
        if IN_JUPYTER:
            if not (token or config):
                cc = ClientConfig()
                # Use production url if none chosen
                prod_url = PRODUCTION_URLS.get(self._server_type, None)
                url = url or cc.default_url or prod_url
                if not cc.get_site_config(url):
                    print("Access token not found.")
                    set_token(url)

        self._available = {}
        self._collection = None
        self._file_options = {}  # type-specific file options (e.g., time variable)
        self._request_inputs = None
        self._request = None
        self._templatefiles = {}
        self._supported_filetypes = ()
        self._downloaded_chunk_sizes = []

        logging_level = get_log_level(logging_level)
        self._logger = getLogger()
        set_stream_handler(self._logger, logging_level)

        self._wps_service = self._create_service_proxy_(config, url, None, None, token)
        # Test if the token is working; re-enter if not
        if IN_JUPYTER:
            invalid_token = True
            attempts = 0
            while invalid_token:
                try:
                    self.list_jobs()
                    invalid_token = False
                except AuthenticationError:
                    print("Token invalid.")
                    attempts += 1
                    if attempts > 3:
                        raise AuthenticationError(AUTH_ERROR_TEXT)
                    set_token(url)
                    self._wps_service = self._create_service_proxy_(
                        config, url, None, None, token
                    )

    def _create_service_proxy_(self, config, url, username, password, token):

        if not isinstance(config, ClientConfig):
            config = ClientConfig(config)

        url = self._check_input(url, "url") or config.default_url
        username = self._check_input(username, "username")
        password = self._check_input(password, "password")
        token = self._check_input(token, "token")

        if not url:
            raise ValueError(
                "The URL must be provided when no default URL is configured."
            )

        if token:
            credentials = {"token": token}
            encode_headers = encode_token_auth
        elif username and password:
            credentials = {"username": username, "password": password}
            encode_headers = encode_basic_auth
        else:
            credentials = config.get_site_config(url)
            if "token" in credentials:
                encode_headers = encode_token_auth
            elif "username" in credentials and "password" in credentials:
                encode_headers = encode_basic_auth
            else:
                encode_headers = encode_no_auth

        # service proxy with authentication
        return ViresWPS10Service(
            url, encode_headers(**credentials), logger=self._logger
        )

    @staticmethod
    def _check_input(value, label):
        if not value:
            return None
        if not isinstance(value, str):
            raise TypeError("%s must be strings" % label)
        return value

    def __str__(self):
        if self._request_inputs is None:
            return "No request set"
        else:
            return self._request_inputs.__str__()

    # @staticmethod
    def _response_handler(
        self, retdatafile, show_progress=True, leave_progress_bar=True
    ):
        """Creates the response handler function for the WPS request

        Streams the remote file to the local (retdatafile),
        with a download progress bar
        """

        def copyfileobj(fsrc, fdst, callback=None, total=None, length=16 * 1024):
            """Copying with progress reporting
            https://stackoverflow.com/a/29967714
            """
            copied = 0
            while True:
                buf = fsrc.read(length)
                if not buf:
                    break
                fdst.write(buf)
                copied += len(buf)
                if callback:
                    callback(copied=copied, total=total)

        def copy_progress(pbar):
            def _copy_progress(copied, total):
                return pbar.update(100 * copied / total)

            return _copy_progress

        def write_response(file_obj):
            """Acts on a file object to copy it to another file
            https://stackoverflow.com/a/7244263
            file_obj is what is returned from urllib.urlopen()
            """
            size = int(file_obj.info()["Content-Length"])
            self._downloaded_chunk_sizes.append(size)
            with ProgressBarDownloading(size, leave=leave_progress_bar) as pbar:
                with open(retdatafile._file.name, "wb") as out_file:
                    copyfileobj(
                        file_obj, out_file, callback=copy_progress(pbar), total=size
                    )

        def write_response_without_reporting(file_obj):
            size = int(file_obj.info()["Content-Length"])
            self._downloaded_chunk_sizes.append(size)
            with open(retdatafile._file.name, "wb") as out_file:
                copyfileobj(file_obj, out_file)

        if show_progress:
            return write_response
        else:
            return write_response_without_reporting

    @staticmethod
    def _chunkify_request(start_time, end_time, sampling_step, nrecords_limit):
        """Split the start and end times into several as necessary, as specified
        by the NRECORDS_LIMIT

        Calculate the maximum number of chunks required
        so that we never request more than nrecords_limit records
        i.e. Consider the time range and the sampling step,
             but neglect that filtering will reduce the number of records
             since we can't predict the effect of filtering beforehand
        Split the requested interval accordingly

        Args:
            start_time (datetime)
            end_time (datetime)
            sampling_step (str) ISO-8601 duration

        Returns:
            list of tuples of datetime pairs,
                e.g. [(start1, end1), (start2, end2)]
        """
        # maximum chunk duration as a timedelta object
        chunk_duration = min(
            timedelta(
                seconds=(nrecords_limit * parse_duration(sampling_step).total_seconds())
            ),
            MAX_CHUNK_DURATION,
        )

        # calculate the chunk intervals ...
        request_intervals = []

        last_time = start_time
        while True:
            next_time = last_time + chunk_duration
            request_intervals.append((last_time, min(next_time, end_time)))
            if next_time >= end_time:
                break
            last_time = next_time

        return request_intervals

    def _get(
        self,
        request=None,
        asynchronous=None,
        response_handler=None,
        message=None,
        show_progress=True,
        leave_progress_bar=True,
    ):
        """Make a request and handle response according to response_handler

        Args:
            request: the rendered xml for the request
            asynchronous (bool): True for asynchronous processing,
                False for synchronous
            response_handler: a function that handles the server response
            message (str): Message to be added to the progress bar
            show_progress (bool): Display progress bars
            leave_progress_bar (bool): Keep displaying after completion
        """
        try:
            if asynchronous:
                if show_progress:
                    with ProgressBarProcessing(
                        message, leave=leave_progress_bar
                    ) as progressbar:
                        return self._wps_service.retrieve_async(
                            request,
                            handler=response_handler,
                            status_handler=progressbar.update,
                        )
                else:
                    return self._wps_service.retrieve_async(
                        request, handler=response_handler
                    )
            else:
                return self._wps_service.retrieve(request, handler=response_handler)
        except WPSError:
            raise RuntimeError(
                "Server error. Or perhaps the request is invalid? "
                "Check the output of: print(request) and "
                "print(request._request.decode())"
            )
        except AuthenticationError:
            raise AuthenticationError(AUTH_ERROR_TEXT)

    def get_between(
        self,
        start_time=None,
        end_time=None,
        filetype="cdf",
        asynchronous=True,
        show_progress=True,
        show_progress_chunks=True,
        leave_intermediate_progress_bars=True,
        nrecords_limit=None,
        tmpdir=None,
    ):
        """Make the server request and download the data.

        Args:
            start_time (datetime / ISO_8601 string)
            end_time (datetime / ISO_8601 string)
            filetype (str): one of ('csv', 'cdf')
            asynchronous (bool): True for asynchronous processing,
                False for synchronous
            show_progress (bool): Set to False to remove progress bars
            show_progress_chunks (bool): Set to False to remove progress bar
                for chunks
            leave_intermediate_progress_bars (bool): Set to False to clean up
                the individual progress bars left when making chunked requests
            nrecords_limit (int): Override the default limit per request
                (e.g. nrecords_limit=3456000)
            tmpdir (str): Override the default temporary file directory

        Returns:
            ReturnedData:
        """
        try:
            start_time = parse_datetime(start_time)
            end_time = parse_datetime(end_time)
        except TypeError:
            raise TypeError(
                "start_time and end_time must be datetime objects or ISO-8601 "
                "date/time strings"
            )

        if end_time < start_time:
            raise ValueError("Invalid time selection! end_time < start_time")

        if asynchronous not in [True, False]:
            raise TypeError("asynchronous must be set to either True or False")

        # Initialise the ReturnedData so that filetype checking is done there
        retdatagroup = ReturnedData(
            filetype=filetype,
            file_options=self._file_options,
        )

        if retdatagroup.filetype not in self._supported_filetypes:
            raise TypeError(f"filetype: {filetype} not supported by server")
        self._request_inputs.response_type = RESPONSE_TYPES[retdatagroup.filetype]

        if asynchronous:
            # asynchronous WPS request
            templatefile = self._templatefiles["async"]
        else:
            # synchronous WPS request
            templatefile = self._templatefiles["sync"]

        # Set the "sampling step" to use to split the request if it's too long
        # (Due to the the server limit of NRECORDS_LIMIT)
        #
        # If a custom sampling step is set, then use that
        try:
            sampling_step_estimate = self._request_inputs.sampling_step
        except AttributeError:
            # Assume 1Hz data otherwise (Currently will use this for Aeolus)
            # Swarm requests all have a sampling_step attribute
            sampling_step_estimate = "PT1S"
        # If no custom sampling step set:
        if sampling_step_estimate is None:
            # Identify a default sampling step if possible
            try:
                collection_key = self._available["collections_to_keys"][
                    self._collection_list[0]
                ]
                sampling_step_estimate = self._available["collection_sampling_steps"][
                    collection_key
                ]
            except Exception:
                sampling_step_estimate = "PT1S"
        nrecords_limit = NRECORDS_LIMIT if nrecords_limit is None else nrecords_limit
        # Split the request into several intervals
        intervals = self._chunkify_request(
            start_time, end_time, sampling_step_estimate, nrecords_limit
        )
        nchunks = len(intervals)
        # Recreate the ReturnedData with the right number of chunks
        retdatagroup = ReturnedData(
            filetype=filetype,
            N=nchunks,
            tmpdir=tmpdir,
            file_options=self._file_options,
        )

        def _get_chunk(i, start_time_i, end_time_i, leave_progress_bar=False):
            """Process an individual chunk and update retdatagroup"""
            message = f"[{i + 1}/{nchunks}] "
            # Finalise the WPSInputs object and (re-)generate the xml
            self._request_inputs.begin_time = start_time_i
            self._request_inputs.end_time = end_time_i
            self._request = self._request_inputs.as_xml(templatefile)
            # Identify the individual ReturnedData object within the group
            retdatafile = retdatagroup.contents[i]
            # Make the request, as either asynchronous or synchronous
            # The response handler streams the data to the ReturnedData object
            response_handler = self._response_handler(
                retdatafile,
                show_progress=show_progress,
                leave_progress_bar=leave_progress_bar,
            )
            self._get(
                request=self._request,
                asynchronous=asynchronous,
                response_handler=response_handler,
                message=message,
                show_progress=show_progress,
                leave_progress_bar=leave_progress_bar,
            )

        if nchunks > 1:
            # Track the size of each chunk as they come in
            self._downloaded_chunk_sizes = []
            if show_progress_chunks:
                with ProgressBarChunks(nchunks) as pbar:
                    totalsize = 0
                    # Get each chunk serially
                    for i, (start_time_i, end_time_i) in enumerate(intervals):
                        pbar.update(i, nchunks, totalsize)
                        _get_chunk(
                            i,
                            start_time_i,
                            end_time_i,
                            leave_progress_bar=leave_intermediate_progress_bars,
                        )
                        totalsize = sum(self._downloaded_chunk_sizes)
                    pbar.update(i, nchunks, totalsize, final=True)
            else:
                for i, (start_time_i, end_time_i) in enumerate(intervals):
                    _get_chunk(i, start_time_i, end_time_i)
        else:
            _get_chunk(0, start_time, end_time, leave_progress_bar=True)

        return retdatagroup

    def list_jobs(self):
        """Return job information from the server.

        Returns:
            dict
        """
        templatefile = TEMPLATE_FILES["list_jobs"]
        template = JINJA2_ENVIRONMENT.get_template(templatefile)
        request = template.render().encode("UTF-8")
        response = self._get(request, asynchronous=False, show_progress=False)
        return json.loads(response.decode("UTF-8"))

    def available_times(self, collection, start_time=None, end_time=None):
        """Returns temporal availability for a given collection

        Args:
            (str): collection name
            start_time (datetime / ISO_8601 string)
            end_time (datetime / ISO_8601 string)

        Returns:
            DataFrame

        """
        template = JINJA2_ENVIRONMENT.get_template(TEMPLATE_FILES["getTimeData"])
        request = template.render(
            collection_id=collection, begin_time=start_time, end_time=end_time
        ).encode("UTF-8")
        response = self._get(request, asynchronous=False, show_progress=False)
        df = read_csv(StringIO(str(response, "utf-8")))
        # Convert to datetime objects
        try:
            df["starttime"] = to_datetime(df["starttime"], format="ISO8601")
            df["endtime"] = to_datetime(df["endtime"], format="ISO8601")
        except ValueError:
            df["starttime"] = to_datetime(df["starttime"])
            df["endtime"] = to_datetime(df["endtime"])
        return df
