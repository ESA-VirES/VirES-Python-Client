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
    """Flexible object for handling data returned from the server.

    Holds the data returned from the server and the data type.
    Provides output to different file types.
    """

    def __init__(self, data=None, filetype=None):
        self.data = bytes() if data is None else data
        self.filetype = str() if filetype is None else filetype
        # In Python 2.7: the above doesn't seem to use the property fset (?)

    def __str__(self):
        return "viresclient ReturnedData object of type " + self.filetype + \
            "\nSave it to a file with .to_file('filename')"

    def data():
        doc = "The data property."
        def fget(self):
            return self._data
        def fset(self, value):
            if not isinstance(value, bytes):
                raise TypeError("data must be of type bytes")
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
            if not isinstance(value, str):
                raise TypeError("filetype must be a string")
            value = value.lower()
            if value not in ("csv", "cdf"):
                raise TypeError("Chosen filetype must be one of: 'csv', 'cdf'")
            self._filetype = value
        def fdel(self):
            del self._filetype
        return locals()
    filetype = property(**filetype())

    def to_file(self, filename, overwrite=False, hdf=False):
        """Saves the data to the specified file.

        Only write to file if it does not yet exist, or if overwrite=True.
        If hdf=True, convert to an HDF5 file.

        Args:
            filename (str): path to the file to save as
            overwrite (bool): Will overwrite existing file if True
            hdf (bool): Will convert to an HDF5 file if True
        """
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
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
        """Convert the data to a pandas DataFrame.

        Note:
            Currently saves a temporary CDF file

        Returns:
            DataFrame

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


class ClientRequest:
    """Handles the requests to and downloads from the server.

    Steps to download data:

    1. Set up a connection to the server with: request = ClientRequest()

    2. Set collections to use with: request.set_collections()

    3. Set parameters to get with: request.set_products()

    4. Set filters to apply with: request.set_range_filter()

    5. Get the data in a chosen time window: request.get_between()

    Args:
        url (str):
        username (str):
        password (str):
        logging_level (str):

    """

    def __init__(self, url=None, username=None, password=None,
                 logging_level="NO_LOGGING"):

        for i in [url, username, password]:
            if not isinstance(i, str):
                raise TypeError(
                    "url, username, and password must all be strings"
                )

        self._tag = []
        self._collections = []
        self._models = []
        self._variables = []
        self._auxiliaries = []
        self._filterlist = []
        self._subsample = None

        self._available = self._set_available_data()

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
            "Collections: {}\nModels: {}\nVariables: {}\n"\
            "Filters: {}\nSubsampling: {}"\
            .format(self._collections, self._models,
                    self._variables, self._filterlist, self._subsample
                    )

    def _set_available_data(self):
        collections_grouped = {
            "MAG": ["SW_OPER_MAG{}_LR_1B".format(x) for x in ("ABC")],
            "EFI": ["SW_OPER_EFI{}_PL_1B".format(x) for x in ("ABC")],
            "IBI": ["SW_OPER_IBI{}TMS_2F".format(x) for x in ("ABC")],
            "TEC": ["SW_OPER_TEC{}TMS_2F".format(x) for x in ("ABC")],
            "FAC": ["SW_OPER_FAC{}TMS_2F".format(x) for x in ("ABC")] +
            ["SW_OPER_FAC_TMS_2F"],
            "EEF": ["SW_OPER_EEF{}TMS_2F".format(x) for x in ("ABC")]
            }
        collections_flat = [
            item for sublist in list(collections_grouped.values())
            for item in sublist
            ]
        # Build the reverse mapping: "SW_OPER_MAGA_LR_1B": "MAG" etc
        collections_to_keys = dict.fromkeys(collections_flat)
        for coll in collections_to_keys:
            for key in list(collections_grouped.keys()):
                if key in coll:
                    collections_to_keys[coll] = key

        measurements = {
            "MAG": "F,dF_AOCS,dF_other,F_error,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_F,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev".split(","),
            "EFI": "v_SC,v_ion,v_ion_error,E,E_error,dt_LP,n,n_error,T_ion,T_ion_error,T_elec,T_elec_error,U_SC,U_SC_error,v_ion_H,v_ion_H_error,v_ion_V,v_ion_V_error,rms_fit_H,rms_fit_V,var_x_H,var_y_H,var_x_V,var_y_V,dv_mtq_H,dv_mtq_V,SAA,Flags_LP,Flags_LP_n,Flags_LP_T_elec,Flags_LP_U_SC,Flags_TII,Flags_Platform,Maneuver_Id".split(","),
            "IBI": "Bubble_Index,Bubble_Probability,Flags_Bubble,Flags_F,Flags_B,Flags_q".split(","),
            "TEC": "GPS_Position,LEO_Position,PRN,L1,L2,P1,P2,S1,S2,Absolute_STEC,Relative_STEC,Relative_STEC_RMS,DCB,DCB_Error".split(","),
            "FAC": "IRC,IRC_Error,FAC,FAC_Error,Flags,Flags_F,Flags_B,Flags_q".split(","),
            "EEF": "EEF,RelErr,flags".split(",")
            }

        models = """
            IGRF12, SIFM, CHAOS-6-Combined, CHAOS-6-Core, CHAOS-6-Static,
            MCO_SHA_2C, MCO_SHA_2D, MCO_SHA_2F, MLI_SHA_2C, MLI_SHA_2D,
            MMA_SHA_2C-Primary, MMA_SHA_2C-Secondary,
            MMA_SHA_2F-Primary, MMA_SHA_2F-Secondary,
            MIO_SHA_2C-Primary, MIO_SHA_2C-Secondary,
            MIO_SHA_2D-Primary, MIO_SHA_2D-Secondary
            """.replace("\n", "").replace(" ", "").split(",")

        auxiliaries = """
            Timestamp, Latitude, Longitude, Radius, Spacecraft,
            SyncStatus, Kp, Dst, IMF_BY_GSM, IMF_BZ_GSM, IMF_V, F10_INDEX,
            OrbitSource, OrbitNumber, AscendingNodeTime,
            AscendingNodeLongitude, QDLat, QDLon, QDBasis, MLT, SunDeclination,
            SunHourAngle, SunRightAscension, SunAzimuthAngle, SunZenithAngle,
            SunLongitude, SunVector, DipoleAxisVector, NGPLatitude, NGPLongitude,
            DipoleTiltAngle, UpwardCurrent, TotalCurrent,
            DivergenceFreeCurrentFunction, F_AMPS, B_NEC_AMPS
            """.replace("\n", "").replace(" ", "").split(",")

        return {
            "collections_grouped": collections_grouped,
            "collections": collections_flat,
            "collections_to_keys": collections_to_keys,
            "measurements": measurements,
            "models": models,
            "auxiliaries": auxiliaries
            }

    def available_collections(self):
        """Returns a list of the available collections.
        """
        return self._available["collections"]

    def available_measurements(self, collection_key=None):
        """Returns a list of the available measurements for the chosen collection.

        Args:
            collection_key (str): one of: ("MAG", "EFI", "IBI", "TEC", "FAC", "EEF")

        """
        keys = list(self._available["measurements"].keys())
        if collection_key in keys:
            return self._available["measurements"][collection_key]
        elif collection_key is None:
            return self._available["measurements"]
        else:
            raise Exception(
                "collection_key must be one of {}".format(", ".join(keys))
                )

    def available_models(self):
        """Returns a list of the available models.
        """
        return self._available["models"]

    def available_auxiliaries(self):
        """Returns a list of the available auxiliary parameters.
        """
        return self._available["auxiliaries"]

    def set_collection(self, collection):
        """Set the collection to use (sets satellite implicitly).

        Note:
            Currently limited to one collection, one satellite.

        Args:
            collection (str): one of .available_collections()

        """
        if collection not in self._available["collections"]:
            raise Exception(
                "Invalid collection. "
                "Check available with ClientRequest.available_collections()")
        else:
            self._tag = "X"
            self._collections = [collection]

    def set_products(self, measurements=None, models=None, auxiliaries=None,
                     residuals=False, subsample=None
                     ):  # change these to all kwargs
        """Set the combination of products to retrieve.

        If residuals=True then just get the measurement-model residuals,
        otherwise get both measurement and model values.

        Args:
            measurements (list(str)): from .available_measurements(collection_key)
            models (list(str)): from .available_models()
            auxiliaries (list(str)): from .available_auxiliaries()
            residuals (bool): True if only returning measurement-model residual
            subsample (str): ISO_8601 duration, e.g. 10 seconds: PT10S, 1 minute: PT1M

        """
        measurements = [] if measurements is None else measurements
        models = [] if models is None else models
        auxiliaries = [] if auxiliaries is None else auxiliaries
        # Check the chosen measurements are available for the set collection
        collection_key = self._available["collections_to_keys"][self._collections[0]]
        for x in measurements:
            if x not in self._available["measurements"][collection_key]:
                raise Exception(
                    "Measurement '{}' not available for collection '{}'. "
                    "Check available with "
                    "ClientRequest.available_measurements({})".format(
                        x, collection_key, collection_key
                    ))
        # Check chosen model is available
        for x in models:
            if x not in self._available["models"]:
                raise Exception(
                    "Model '{}' not available. Check available with "
                    "ClientRequest.available_models()".format(x)
                    )
        # Check chosen aux is available
        for x in auxiliaries:
            if x not in self._available["auxiliaries"]:
                raise Exception(
                    "'{}' not available. Check available with "
                    "ClientRequest.available_auxiliaries()".format(x)
                    )
        # TODO: check format of all inputs
        self._measurements = measurements
        self._models = models
        self._auxiliaries = auxiliaries
        self._subsample = subsample
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
        """Set a filter to apply.

        Note:
            Apply multiple filters with successive calls to set_range_filter()

        Args:
            parameter (str)
            minimum (float)
            maximum (float)

        """
        self._filterlist += [parameter+":"+str(minimum)+","+str(maximum)]

    def get_times_for_orbits(self, spacecraft, start_orbit, end_orbit):
        """Translate a pair of orbit numbers to a time interval.

        Args:
            spacecraft (str): one of ('A','B','C') or
                                ("Alpha", "Bravo", "Charlie")
            start_orbit (int): a starting orbit number
            end_orbit (int): a later orbit number

        Returns:
            tuple(datetime): (start_time, end_time) The start time of the
                start_orbit and the ending time of the end_orbit.
                (Based on ascending nodes of the orbits)

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
        """Translate a time to an orbit number.

        Args:
            spacecraft (str): one of ('A','B','C') or
                                ("Alpha", "Bravo", "Charlie")
            input_time (datetime): a point in time

        Returns:
            int: The current orbit number at the input_time

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
        """Make the server request and download the data.

        Args:
            start_time (datetime)
            end_time (datetime)
            filetype (str): one of ('csv', 'cdf')
            async (bool): True for asynchronous processing, False for synchronous

        Returns:
            ReturnedData object

        """
        self.start_time = start_time
        self.end_time = end_time

        if len(self._filterlist) == 1:
            self._filters = self._filterlist[0]
        else:
            self._filters = ';'.join(self._filterlist)

        if async not in [True, False]:
            raise TypeError("async must be set to either True or False")

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
            subsample=self._subsample
        ).encode('UTF-8')

        if async:
            with ProgressBar() as progressbar:
                response = self._wps.retrieve_async(
                    self.request, status_handler=progressbar.update
                )
        else:
            response = self._wps.retrieve(self.request)

        retdata.data = response
        return retdata
