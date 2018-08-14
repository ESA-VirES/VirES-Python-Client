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
import tempfile
import shutil

import numpy
import pandas
import xarray
import cdflib

from ._wps import time_util
# from viresclient import VIRESCLIENT_DEFAULT_FILE_DIR

CDF_EPOCH_1970 = 62167219200000.0


def _fix_Dataset_column(da):
    """
    If column (i.e. a DataArray) is 1D (i.e. consists of scalars):
    Attach 'times' as the coordinates
    If column is 2D:
    Convert the DataArray from a stack of lists to a ND array
    Attach 'time' and 'dim':(0,1,2,..) as the coordinates
    """
    data = numpy.stack(da.values)
    times = da.coords['Timestamp'].values
#     lats = da['Latitude'].values
#     lons = da['Longitude'].values
    if len(data.shape) == 1:
        # scalars
        return xarray.DataArray(data, coords=[times], dims=['time'])
    elif len(data.shape) == 2:
        # N-dimensional vectors will be labelled with 0,1,2...
        locs = [i for i in range(data.shape[1])]
#         locs = ['N','E','C']  # could be introduced depending on the column name
        return xarray.DataArray(data,
                                coords=[times, locs],
                                dims=['time', 'dim']
                                )
    else:
        raise NotImplementedError("Array too complicated...")


def _DataFrame_to_xarrayDataset(df):
    """Convert pandas DataFrame to xarray Dataset
    """
    # Transfer to Dataset
    ds = xarray.Dataset.from_dataframe(df)
    # Change vector columns accordingly and set coordinates (time,dim)
    ds = xarray.Dataset(
        {column: _fix_Dataset_column(ds[column]) for column in df}
        )
    return ds


class ReturnedData(object):
    """Flexible object for handling data returned from the server.

    Holds the data returned from the server and the data type.
    Data is held in a NamedTemporaryFile. It is automatically closed & destroyed
     when it goes out of scope.
    Provides output to different file types and data objects.
    """

    def __init__(self, filetype=None):
        self._supported_filetypes = ("csv", "cdf", "nc")
        self.filetype = str() if filetype is None else filetype
        # SpooledTemporaryFile may be quicker on very small file sizes (<1MB?)
        # Depends on the machine it is running on - choose the directory of the temp file?
        # But need to do some extra work for cdf->dataframe support
        # self._file = tempfile.SpooledTemporaryFile(max_size=1e8)
        self._file = tempfile.NamedTemporaryFile()
        # Add an option for storing to a regular file directly?

    def __str__(self):
        return "viresclient ReturnedData object of type " + self.filetype + \
            "\nSave it to a file with .to_file('filename')" + \
            "\nLoad it as a pandas dataframe with .as_dataframe()" + \
            "\nLoad it as an xarray dataset with .as_xarray()"

    @property
    def file(self):
        self._file.seek(0)
        return self._file

    # @property
    # def _data(self):
    #     self.file.seek(0)
    #     return self.file.read()

    def _write_new_data(self, data):
        """Replace the tempfile contents with 'data' (bytes)
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be of type bytes")
        self.file.seek(0)
        self.file.write(data)

    def _write_file(self, filename):
        """Write the tempfile out to a regular file
        """
        self.file.seek(0)
        with open(filename, 'wb') as out_file:
            shutil.copyfileobj(self.file, out_file)

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        if not isinstance(value, str):
            raise TypeError("filetype must be a string")
        value = value.lower()
        if value not in self._supported_filetypes:
            raise TypeError("Chosen filetype must be one of: {}".format(
                            self._supported_filetypes
                            ))
        self._filetype = value

    @staticmethod
    def _check_outfile(path, path_extension, overwrite=False):
        """Check validity of path and extension, and if it exists already
        """
        if not isinstance(path, str):
            raise TypeError("path must be a string")
        if path.split('.')[-1].lower() != path_extension:
            raise TypeError("Filename extension should be {}".format(
                path_extension
                ))
        if isfile(path) and not overwrite:
            raise Exception(
                "File not written as it already exists and overwrite=False"
                )

    def to_file(self, path, overwrite=False):
        """Saves the data to the specified file.

        Only write to file if it does not yet exist, or if overwrite=True.
        Currently handles CSV and CDF formats.

        Args:
            path (str): path to the file to save as
            overwrite (bool): Will overwrite existing file if True
        """
        self._check_outfile(path, self.filetype, overwrite)
        self._write_file(path)
        print("Data written to", path)

    # def to_hdf(self, path, overwrite=False):
    #     """Saves the data as an HDF5 file
    #
    #     Extension should be .h5
    #     """
    #     self._check_outfile(path, 'h5', overwrite)
    #     # Convert to dataframe.
    #     df = self.as_dataframe()
    #     df.to_hdf(path, "data", mode="w")
    #     print("Data written to", path)

    def to_netcdf(self, path, overwrite=False):
        """Saves the data as a netCDF4 file (this is compatible with HDF5)

        Extension should be .nc
        """
        self._check_outfile(path, 'nc', overwrite)
        # Convert to xarray Dataset
        ds = self.as_xarray()
        ds.to_netcdf(path)
        print("Data written to", path)

    def as_dataframe(self):
        """Convert the data to a pandas DataFrame.

        Returns:
            DataFrame

        """
        if self.filetype == 'csv':
            try:
                # df = pandas.read_csv(BytesIO(self._data))
                df = pandas.read_csv(self.file.name)
            except Exception:
                raise Exception("Bad or empty csv.")
            # Convert to datetime objects
            df['Timestamp'] = df['Timestamp'].apply(
                time_util.parse_datetime
                )
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
            # Currently need to write to a *named* temporary file,
            # in order to use cdflib (which requires a file name to point to)
            try:
                cdf = cdflib.CDF(self.file.name)
                keys = cdf.cdf_info()['zVariables']
                vals = [cdf.varget(key) for key in keys]
            except Exception:
                raise Exception("Bad or empty cdf.")
            if all(v is None for v in vals):
                # Returns empty dataframe when retrieval from server is empty
                df = pandas.DataFrame(columns=keys)
                print("No data available")
            else:
                # Set up the output dataframe
                # Convert timestamps to datetime objects
                d = {key: list(value) for key, value in zip(keys, vals)}
                df = pandas.DataFrame.from_dict(d)
                df['Timestamp'] = df['Timestamp'].apply(
                    lambda x: time_util.unix_epoch_to_datetime(
                        (x-CDF_EPOCH_1970)*1e-3
                        )
                    )
        df.set_index('Timestamp', inplace=True)
        return df

    def as_xarray(self, group=None):
        """Convert the data to an xarray Dataset.

        Note:
            For CSV and CDF, currently goes via a DataFrame

        Returns:
            Dataset

        """
        if self.filetype in ('cdf', 'csv'):
            ds = _DataFrame_to_xarrayDataset(self.as_dataframe())
        elif self.filetype == 'nc':
            ds = xarray.open_dataset(self.file.name, group=group)
        return ds


class ReturnedDataGroup(object):
    """Holds a list of ReturnedData objects
    """

    def __init__(self, filetype=None, N=1):
        self.filetype = filetype
        self.contents = [ReturnedData(filetype=filetype) for i in range(N)]

    def as_dataframe(self):
        """Convert the data to a pandas DataFrame.

        Returns:
            DataFrame

        """
        return pandas.concat([d.as_dataframe() for d in self.contents])

    def as_xarray(self):
        """Convert the data to an xarray Dataset.

        Note:
            For CSV and CDF, currently goes via a DataFrame

        Returns:
            Dataset

        """
        return _DataFrame_to_xarrayDataset(self.as_dataframe())

    def to_files(self, paths, overwrite=False):
        """Saves the data to the specified files.

        Only write to file if it does not yet exist, or if overwrite=True.
        Currently handles CSV and CDF formats.

        Args:
            paths (list of str): paths to the files to save as
            overwrite (bool): Will overwrite existing file if True
        """
        nfiles = len(self.contents)
        if not isinstance(paths, list) or not isinstance(paths[0], str):
            raise TypeError("paths must be a list of strings")
        if len(paths) != nfiles:
            raise Exception(
                "Number of paths must equal number of files ({})".format(
                    nfiles
                ))
        for path, retdata in zip(paths, self.contents):
            retdata.to_file(path, overwrite)

    def to_file(self, path, overwrite=False):
        """Saves the data to the specified file, when data is only in one file.

        Only write to file if it does not yet exist, or if overwrite=True.
        Currently handles CSV and CDF formats.

        Args:
            path (str): path to the file to save as
            overwrite (bool): Will overwrite existing file if True
        """
        if len(self.contents) != 1:
            raise Exception("Data is split into multiple files. "
                            "Use .to_files instead"
                            )
        self.contents[0].to_file(path, overwrite)
