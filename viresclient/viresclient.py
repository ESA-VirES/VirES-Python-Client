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
from os.path import isfile#, join, dirname
from .wps.wps_vires import ViresWPS10Service
# from .wps.time_util import parse_datetime
from .wps.http_util import encode_basic_auth
from logging import getLogger, DEBUG, INFO
from .wps.log_util import set_stream_handler
# from jinja2 import Environment, FileSystemLoader
from .wps.environment import JINJA2_ENVIRONMENT
from .wps import time_util
import json
import pandas
import datetime
try:
    from io import BytesIO
except ImportError:
    # Python 2 backward compatibility
    import StringIO as BytesIO
import cdflib

CDF_EPOCH_1970 = 62167219200000.0


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
                print("Data written to", filename)
            elif hdf:
                if filename[-3:] != ".h5":
                    raise Exception("Filename extension should be .h5")
                # Convert to dataframe.
                df = self.as_dataframe()
                df.to_hdf(filename, "data", mode="w")
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


class ClientRequest:
    """Handles the requests to and downloads from the server.
    """

    def __init__(self, url=None, username=None, password=None, log=0):

        try:
            assert isinstance(url, str)
            assert isinstance(username, str)
            assert isinstance(password, str)
        except AssertionError as e:
            e.args += ("url, username, and password must all be strings",)
            raise

        self.spacecraft = ''
        self.collections = []
        self.models = []
        self.variables = []
        self.auxiliaries = []
        self.filterlist = []

        if log == 0:
            # service proxy with basic HTTP authentication
            self._wps = ViresWPS10Service(
                url,
                encode_basic_auth(username, password)
            )
        else:
            if log == 1:
                loglevel = INFO
            elif log == 2:
                loglevel = DEBUG
            else:
                raise Exception("log must be set to 0, 1, or 2")
            # setting up console logging (optional)
            self._logger = getLogger()
            set_stream_handler(self._logger, loglevel)
            self._logger.debug("TEST LOG MESSAGE")

            # service proxy with basic HTTP authentication
            self._wps = ViresWPS10Service(
                url,
                encode_basic_auth(username, password),
                logger=self._logger
            )

    def __str__(self):
        return "Request details:\n"\
            "Collections: {}, {}\nModels: {}\nVariables: {}\nFilters: {}"\
            .format(self.spacecraft, self.collections, self.models,
                    self.variables, self.filterlist
                    )

    def set_collections(self, spacecraft, collections):
        self.spacecraft = spacecraft
        self.collections = collections

    def set_products(self, measurements, models, auxiliaries, residuals=False):
        """Set the combination of products to retrieve.
        If residuals=True then just get the measurement-model residuals,
        otherwise get both measurement and model values
        """
        self.measurements = measurements
        self.models = models
        self.auxiliaries = auxiliaries
        # Set up the variables that actually get passed to the WPS request
        variables = []
        if not residuals:
            variables += self.measurements
            # Model values
            for model_name in self.models:
                for measurement in self.measurements:
                    variables += ["%s_%s" % (measurement, model_name)]
        elif residuals:
            # Model residuals
            for model_name in self.models:
                for measurement in self.measurements:
                    variables += ["%s_res_%s" % (measurement, model_name)]
        variables += self.auxiliaries
        self.variables = variables

    def set_range_filter(self, parameter, minimum, maximum):
        self.filterlist += [parameter+":"+str(minimum)+","+str(maximum)]

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
        assert spacecraft in ("Alpha", "Bravo", "Charlie")
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

        if len(self.filterlist) == 1:
            self.filters = self.filterlist[0]
        else:
            self.filters = ';'.join(self.filterlist)

        try:
            assert async in [True, False]
        except AssertionError as e:
            e.args += ("async must be set to either True or False",)
            raise

        # Initialise the ReturnedData so that filetype checking is done there
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
        self.template = JINJA2_ENVIRONMENT.get_template(templatefile)

        self.request = self.template.render(
            begin_time=self.start_time,
            end_time=self.end_time,
            model_ids=self.models,
            variables=self.variables,
            collection_ids={self.spacecraft: self.collections},
            filters=self.filters,
            response_type=self.response_type,
        ).encode('UTF-8')

        if async:
            response = self._wps.retrieve_async(self.request) #(self.request, handler= ...)
        else:
            response = self._wps.retrieve(self.request)

        retdata.data = response
        return retdata
