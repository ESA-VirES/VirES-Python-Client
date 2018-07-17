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
try:
    from io import BytesIO
except ImportError:
    # Python 2 backward compatibility
    import StringIO as BytesIO

import pandas
import cdflib

from ._wps import time_util

CDF_EPOCH_1970 = 62167219200000.0


class ReturnedData(object):
    """Flexible object for handling data returned from the server.

    Holds the data returned from the server and the data type.
    Provides output to different file types.
    """

    def __init__(self, data=None, filetype=None):
        self.data = bytes() if data is None else data
        self.filetype = str() if filetype is None else filetype

    def __str__(self):
        return "viresclient ReturnedData object of type " + self.filetype + \
            "\nSave it to a file with .to_file('filename')"

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if not isinstance(value, bytes):
            raise TypeError("data must be of type bytes")
        self._data = value

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        if not isinstance(value, str):
            raise TypeError("filetype must be a string")
        value = value.lower()
        if value not in ("csv", "cdf"):
            raise TypeError("Chosen filetype must be one of: 'csv', 'cdf'")
        self._filetype = value

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
                    raise TypeError("Filename extension should be {}".format(
                        self.filetype.upper()
                        ))
                with open(filename, "wb") as f:
                    f.write(self.data)
            elif hdf:
                if filename[-3:] != ".h5":
                    raise TypeError("Filename extension should be .h5")
                # Convert to dataframe.
                df = self.as_dataframe()
                df.to_hdf(filename, "data", mode="w")
            print("Data written to", filename)
        else:
            # raise FileExistsError(    # doesn't exist in py27
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
            try:
                df = pandas.read_csv(BytesIO(self.data))
            except Exception:
                # print("Bad or empty csv. Returning an empty dataframe.")
                # return pandas.DataFrame()
                raise Exception("Bad or empty csv.")
            # Convert to datetime objects
            df['Timestamp'] = df['Timestamp'].apply(
                time_util.parse_datetime
                )
            # # Originally used MJD2000 from the server:
            # df['Timestamp'] = df['Timestamp'].apply(
            #     time_util.mjd2000_to_datetime
            #     )
            # # Rounded because the MJD2000 fractions are not precise enough(?)
            # df['Timestamp'] = df['Timestamp'].dt.round('1s')
            # Convert the columns of vectors from strings to lists
            if len(df) == 0:
                # Returns empty dataframe when retrieval from server is empty
                print("No data available")
            else:
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
            try:
                cdf = cdflib.CDF('cdftempfile.CDF')
                keys = cdf.cdf_info()['zVariables']
                vals = [cdf.varget(key) for key in keys]
            except Exception:
                # print("Bad or empty cdf. Returning an empty dataframe.")
                remove('cdftempfile.CDF')
                # return pandas.DataFrame()
                raise Exception("Bad or empty cdf.")
            if all(v is None for v in vals):
                # Returns empty dataframe when retrieval from server is empty
                df = pandas.DataFrame(columns=keys)
                print("No data available")
            else:
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
