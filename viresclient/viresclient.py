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


from os import remove
from os.path import isfile  # , join, dirname
import datetime
try:
    from io import BytesIO
except ImportError:
    # Python 2 backward compatibility
    import StringIO as BytesIO

import json
import pandas
import cdflib
from tqdm import tqdm

from .wps.wps_vires import ViresWPS10Service
# from .wps.time_util import parse_datetime
from .wps.http_util import encode_basic_auth
from logging import getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
from .wps.log_util import set_stream_handler
# from jinja2 import Environment, FileSystemLoader
from .wps.environment import JINJA2_ENVIRONMENT
from .wps import time_util

CDF_EPOCH_1970 = 62167219200000.0

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


class ReturnedData:
    """Holds the data returned from the server and the data type.
    Provides output to different file types.
    """

    def __init__(self, data=bytes(), filetype=str()):
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
                assert value in ("csv", "cdf")
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

    def to_file(self, filename, overwrite=False, hdf=False):
        """Saves the data to the specified file.
        Only write to file if it does not yet exist, or if overwrite=True.
        If hdf=True, convert to an HDF5 file.
        """
        try:
            assert isinstance(filename, str)
        except AssertionError as e:
            e.args += ("filename must be a string",)
            raise
        if not isfile(filename) or overwrite:
            if not hdf:
                if filename[-3:].lower() != self.filetype:
                    raise Exception("Filename extension should be {}".format(
                        self.filetype.upper()
                        ))
                with open(filename, "wb") as f:
                    f.write(self.data)
            elif hdf:
                if filename[-3:] != ".h5":
                    raise Exception("Filename extension should be .h5")
                # Convert to dataframe.
                df = self.as_dataframe()
                df.to_hdf(filename, "data", mode="w")
            print("Data written to", filename)
        else:
            raise Exception(
                "File not written as it already exists and overwrite=False"
                )

    def as_dataframe(self):
        """Convert the data to a pandas DataFrame
        NB: currently saves a temporary CDF file
        """
        if self.filetype == 'csv':
            df = pandas.read_csv(BytesIO(self.data))
            df['Timestamp'] = df['Timestamp'].apply(
                time_util.mjd2000_to_datetime
                )
            # Rounded because the MJD2000 fractions are not precise enough(?)
            df['Timestamp'] = df['Timestamp'].dt.round('1s')
            # Convert the columns of vectors from strings to lists
            for col in df:
                if type(df[col][0]) is str:
                    if df[col][0][0] == '{':
                        df[col] = df[col].apply(
                            lambda x: [
                                float(y) for y in x.strip('{}').split(';')
                            ])
        elif self.filetype == 'cdf':
            self.to_file('cdftempfile.CDF', overwrite=True)
            cdf = cdflib.CDF('cdftempfile.CDF')
            keys = cdf.cdf_info()['zVariables']
            vals = [cdf.varget(key) for key in keys]
            d = {key: list(value) for key, value in zip(keys, vals)}
            df = pandas.DataFrame.from_dict(d)
            df['Timestamp'] = df['Timestamp'].apply(
                lambda x: time_util.unix_epoch_to_datetime(
                    (x-CDF_EPOCH_1970)*1e-3
                    )
                )
            remove('cdftempfile.CDF')
            print("Removed cdftempfile.CDF")
        df.set_index('Timestamp', inplace=True)
        return df


class ProgressBar:
    """Generates a progress bar from the WPS status
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

    def cleanup(self):
        self.tqdm_pbar.close()

    def update(self, wpsstatus):
        """Updates the state based on the state of a WPSStatus object
        """
        self.lastpercent = self.percentCompleted
        self.percentCompleted = wpsstatus.percentCompleted
        if self.lastpercent != self.percentCompleted:
            self.refresh_tqdm()

    def refresh_tqdm(self):
        if self.percentCompleted is None:
            return
        self.tqdm_pbar.update(self.percentCompleted-self.lastpercent)
        if self.percentCompleted == 100:
            self.cleanup()
            print('Downloading...')


class ClientRequest:
    """Handles the requests to and downloads from the server.
    """

    def __init__(self, url=None, username=None, password=None,
                 logging_level="NO_LOGGING"):

        try:
            assert isinstance(url, str)
            assert isinstance(username, str)
            assert isinstance(password, str)
        except AssertionError as e:
            e.args += ("url, username, and password must all be strings",)
            raise

        self._tag = []
        self._collections = []
        self._models = []
        self._variables = []
        self._auxiliaries = []
        self._filterlist = []

        logging_level = get_log_level(logging_level)
        self._logger = getLogger()
        set_stream_handler(self._logger, logging_level)

        # service proxy with basic HTTP authentication
        self._wps = ViresWPS10Service(
            url,
            encode_basic_auth(username, password),
            logger=self._logger
        )

    def __str__(self):
        return "Request details:\n"\
            "Collections: {}\nModels: {}\nVariables: {}\nFilters: {}"\
            .format(self._collections, self._models,
                    self._variables, self._filterlist
                    )

    def set_collection(self, collection):
        self._tag = "X"
        self._collections = [collection]

    def set_products(self, measurements, models, auxiliaries, residuals=False):
        """Set the combination of products to retrieve.
        If residuals=True then just get the measurement-model residuals,
        otherwise get both measurement and model values
        """
        self._measurements = measurements
        self._models = models
        self._auxiliaries = auxiliaries
        # Set up the variables that actually get passed to the WPS request
        variables = []
        if not residuals:
            variables += self._measurements
            # Model values
            for model_name in self._models:
                for measurement in self._measurements:
                    variables += ["%s_%s" % (measurement, model_name)]
        elif residuals:
            # Model residuals
            for model_name in self._models:
                for measurement in self._measurements:
                    variables += ["%s_res_%s" % (measurement, model_name)]
        variables += self._auxiliaries
        self._variables = variables

    def set_range_filter(self, parameter, minimum, maximum):
        self._filterlist += [parameter+":"+str(minimum)+","+str(maximum)]

    def get_times_for_orbits(self, spacecraft, start_orbit, end_orbit):
        """Translate a pair of orbit numbers to a time interval
        """
        # Change to spacecraft = "A" etc. for this request
        if spacecraft in ("Alpha", "Bravo", "Charlie"):
            spacecraft = spacecraft[0]
        templatefile = "vires_times_from_orbits.xml"
        template = JINJA2_ENVIRONMENT.get_template(templatefile)
        request = template.render(
            spacecraft=spacecraft,
            start_orbit=start_orbit,
            end_orbit=end_orbit
        ).encode('UTF-8')
        response = self._wps.retrieve(request)
        responsedict = json.loads(response.decode('UTF-8'))
        start_time = time_util.parse_datetime(responsedict['start_time'])
        end_time = time_util.parse_datetime(responsedict['end_time'])
        return start_time, end_time

    def get_orbit_number(self, spacecraft, input_time):
        """Translate a time to an orbit number
        """
        # Change to spacecraft = "A" etc. for this request
        if spacecraft in ("Alpha", "Bravo", "Charlie"):
            spacecraft = spacecraft[0]
        collections = ["SW_OPER_MAG{}_LR_1B".format(spacecraft[0])]
        templatefile = "test_vires_fetch_filtered_data.xml"
        template = JINJA2_ENVIRONMENT.get_template(templatefile)
        request = template.render(
            begin_time=input_time,
            end_time=input_time+datetime.timedelta(seconds=1),
            model_ids=[],
            variables=["OrbitNumber"],
            collection_ids={spacecraft: collections},
            filters=[],
            response_type="text/csv",
        ).encode('UTF-8')
        response = self._wps.retrieve(request)
        retdata = ReturnedData(data=response, filetype="csv")
        return retdata.as_dataframe()["OrbitNumber"][0]

    def get_between(self, start_time, end_time, filetype="csv", async=True):
        self.start_time = start_time
        self.end_time = end_time

        if len(self._filterlist) == 1:
            self._filters = self._filterlist[0]
        else:
            self._filters = ';'.join(self._filterlist)

        try:
            assert async in [True, False]
        except AssertionError as e:
            e.args += ("async must be set to either True or False",)
            raise

        # Initialise the ReturnedData so that filetype checking is done there
        retdata = ReturnedData(filetype=filetype)
        self._filetype = retdata.filetype

        if self._filetype == "csv":
            self._response_type = "text/csv"
        elif self._filetype == "cdf":
            self._response_type = "application/x-cdf"

        if async:
            # asynchronous WPS request
            templatefile = "test_vires_fetch_filtered_data_async.xml"
        else:
            # synchronous WPS request
            templatefile = "test_vires_fetch_filtered_data.xml"
        self._template = JINJA2_ENVIRONMENT.get_template(templatefile)

        self.request = self._template.render(
            begin_time=self.start_time,
            end_time=self.end_time,
            model_ids=self._models,
            variables=self._variables,
            collection_ids={self._tag: self._collections},
            filters=self._filters,
            response_type=self._response_type,
        ).encode('UTF-8')

        if async:
            # Ensure that tqdm progress bar is removed
            # Could also add __enter__ and __exit__ to ProgressBar
            #   so that it could be used with a 'with' statement?
            try:
                progressbar = ProgressBar()
                response = self._wps.retrieve_async(
                            self.request, status_handler=progressbar.update
                            )  # handler= ...)
            finally:
                # does this imply closing the tqdm bar?
                del progressbar
        else:
            response = self._wps.retrieve(self.request)

        retdata.data = response
        return retdata
