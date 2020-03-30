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

import os
import tempfile
import shutil
import numpy
import pandas
import xarray
import cdflib
from ._wps import time_util
if os.name == "nt":
    import atexit

CDF_EPOCH_1970 = 62167219200000.0

# Frame names to use as xarray dimension names
FRAME_NAMES = {"NEC": ["B_NEC"],
               "VFM": ["B_VFM", "dB_Sun", "dB_AOCS", "dB_other", "B_error"],
               "quaternion": ["q_NEC_CRF"],
               "WGS84": ["GPS_Position", "LEO_Position"],
               "EEJ_QDLat": ["EEJ"]}
# Reverse mapping of the above
DATANAMES_TO_FRAME_NAMES = {}
for framename, datanameset in FRAME_NAMES.items():
    for dataname in datanameset:
        DATANAMES_TO_FRAME_NAMES[dataname] = framename
# Labels to use for suffixes on expanded columns in pandas dataframe
#   and on dimension coordinates in xarray
FRAME_LABELS = {"NEC": ["N", "E", "C"],
                "VFM": ["i", "j", "k"],
                "quaternion": ["1", "i", "j", "k"],
                "WGS84": ["X", "Y", "Z"],
                "EEJ_QDLat": numpy.linspace(-20, 20, 81)}
FRAME_DESCRIPTIONS = {
    "NEC": "NEC frame - North, East, Centre (down)",
    "VFM": "Vector Field Magnetometer instrument frame",
    "EEJ_QDLat": "Quasi-dipole latitude profile between -20 and 20 degrees from the EEF product"
}


class FileReader(object):
    """Provides access to file contents (wrapper around cdflib)
    """

    def __init__(self, file, filetype="cdf"):
        """

        Args:
            file (file-like or str)
        """
        if filetype.lower() == "cdf":
            self._cdf = self._open_cdf(file)
            globalatts = self._cdf.globalattsget()
            self.sources = self._ensure_list(
                globalatts.get('ORIGINAL_PRODUCT_NAMES', []))
            self.magnetic_models = self._ensure_list(
                globalatts.get('MAGNETIC_MODELS', []))
            self.range_filters = self._ensure_list(
                globalatts.get('DATA_FILTERS', []))
            self.variables = self._cdf.cdf_info()['zVariables']
            self._varatts = {var: self._cdf.varattsget(var)
                             for var in self.variables}
            self._varinfo = {var: self._cdf.varinq(var)
                             for var in self.variables}
        else:
            raise NotImplementedError("{} not supported".format(filetype))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._cdf.close()

    @staticmethod
    def _open_cdf(file):
        try:
            return cdflib.CDF(file.name)
        except AttributeError:
            return cdflib.CDF(file)

    @staticmethod
    def _ensure_list(attribute):
        if isinstance(attribute, str):
            return [attribute]
        else:
            return attribute

    def get_variable(self, var):
        try:
            data = self._cdf.varget(var)
        except ValueError:
            data = None
        if data is None:
            shape = [0, *self.get_variable_dimsizes(var)]
            data = numpy.empty(shape)
        return data

    def get_variable_units(self, var):
        return self._varatts[var].get("UNITS", None)

    def get_variable_description(self, var):
        return self._varatts[var].get("DESCRIPTION", None)

    def get_variable_numdims(self, var):
        return self._varinfo[var].get("Num_Dims")

    def get_variable_dimsizes(self, var):
        return self._varinfo[var].get("Dim_Sizes")

    @staticmethod
    def _cdftime_to_datetime(t):
        try:
            return pandas.to_datetime(
                (t - CDF_EPOCH_1970)/1e3,
                unit='s'
            )
        except TypeError:
            return []

    def as_pandas_dataframe(self, expand=False):
        # Use the variables in the file as columns to create in the dataframe.
        # Skip Timestamp as it will be used as the index.
        columns = set(self.variables)
        columns.remove("Timestamp")
        # Split columns according to those to be expanded into multiple columns
        columns_to_expand = set(c for c in columns
                                if c in DATANAMES_TO_FRAME_NAMES.keys()
                                or "B_NEC" in c) if expand else set()
        columns_standard = columns.difference(columns_to_expand)
        # Initialise dataframe with Timestamp as index
        df = pandas.DataFrame(index=self.get_variable("Timestamp"))
        df.index.name = "Timestamp"
        # Return empty dataframe, including column names
        #  when retrieval from server is empty
        if len(df.index) == 0:
            for column in columns_standard:
                df[column] = None
            for column in columns_to_expand:
                framename = DATANAMES_TO_FRAME_NAMES.get(column, "NEC")
                suffixes = FRAME_LABELS[framename]
                for suffix in suffixes:
                    df[column + "_" + str(suffix)] = None
            return df
        # Convert timestamps to datetime objects
        df.index = self._cdftime_to_datetime(df.index)
        # Separately add non-expanded and expanded columns
        for column in columns_standard:
            df[column] = list(self.get_variable(column))
        for column in columns_to_expand:
            vector_data = self.get_variable(column)
            framename = DATANAMES_TO_FRAME_NAMES.get(column, "NEC")
            suffixes = FRAME_LABELS[framename]
            if len(vector_data.shape) > 2:
                raise NotImplementedError("{}".format(column))
            if vector_data.shape[1] != len(suffixes):
                raise NotImplementedError("{}".format(column))
            for i, suffix in enumerate(suffixes):
                df[column + "_" + str(suffix)] = vector_data[:, i]
        return df

    def as_xarray_dataset(self):
        # NB currrently does not set the global metadata (attrs)
        #  (avoids issues with concatenating them)
        #  (this is done in ReturnedData)
        # Initialise dataset with time coordinate
        ds = xarray.Dataset(
            coords={"Timestamp":
                    self._cdftime_to_datetime(self.get_variable("Timestamp"))})
        # Add Spacecraft variable as Categorical to save memory
        ds["Spacecraft"] = (("Timestamp",), pandas.Categorical(
            self.get_variable("Spacecraft"), categories=["A", "B", "C", "-"]))
        datanames = set(self.variables)
        datanames.remove("Timestamp")
        datanames.remove("Spacecraft")
        # Loop through each variable available and append them to the Dataset,
        #  attaching the Timestamp coordinate to each.
        # Attach dimension names based on the name of the variable,
        #  with coordinate labels if available.
        dims_used = set()
        for dataname in datanames:
            data = self.get_variable(dataname)
            numdims = self.get_variable_numdims(dataname)
            # 1D case (scalar series)
            if numdims == 0:
                ds[dataname] = (("Timestamp",), data)
            # 2D case (vector series)
            elif numdims == 1:
                if "B_NEC" in dataname:
                    dimname = "NEC"
                    dims_used.add(dimname)
                elif dataname in DATANAMES_TO_FRAME_NAMES.keys():
                    dimname = DATANAMES_TO_FRAME_NAMES[dataname]
                    dims_used.add(dimname)
                else:
                    dimname = "%s_dim1" % dataname
                ds[dataname] = (("Timestamp", dimname),
                                self.get_variable(dataname))
            # 3D case (matrix series), e.g. QDBasis
            elif numdims == 2:
                dimname1 = "%s_dim1" % dataname
                dimname2 = "%s_dim2" % dataname
                ds[dataname] = (("Timestamp", dimname1, dimname2),
                                self.get_variable(dataname))
            else:
                raise NotImplementedError("%s: array too complicated" %
                                          dataname)
        # Add named coordinates
        for dimname, dimlabels in FRAME_LABELS.items():
            if dimname in dims_used:
                ds[dimname] = numpy.array(dimlabels)
                ds[dimname].attrs["description"] = FRAME_DESCRIPTIONS.get(
                    dimname, None)
                ds = ds.set_coords(dimname)
        # Add metadata of each variable
        for dataname in ds:
            ds[dataname].attrs["units"] = self.get_variable_units(dataname)
            ds[dataname].attrs["description"] = self.get_variable_description(
                dataname)
        return ds


def make_pandas_DataFrame_from_csv(csv_filename):
    """Load a csv file into a pandas.DataFrame

    Set the Timestamp as a datetime index.

    Args:
        csv_filename (str)

    Returns:
        pandas.DataFrame

    """
    try:
        df = pandas.read_csv(csv_filename)
    except Exception:
        raise Exception("Bad or empty csv.")
    # Convert to datetime objects
    df['Timestamp'] = df['Timestamp'].apply(
        time_util.parse_datetime)
    # Convert the columns of vectors from strings to lists
    # Returns empty dataframe when retrieval from server is empty
    if len(df) != 0:
        # Convert the columns of vectors from strings to lists
        for col in df:
            if type(df[col][0]) is str:
                if df[col][0][0] == '{':
                    df[col] = df[col].apply(
                        lambda x: [
                            float(y) for y in x.strip('{}').split(';')
                        ])
    df.set_index('Timestamp', inplace=True)
    return df


class ReturnedDataFile(object):
    """For handling individual files returned from the server.

    Holds the data returned from the server and the data type.
    Data is held in a NamedTemporaryFile, which is automatically closed and
    destroyed when it goes out of scope.
    Provides output to different file types and data objects.

    """

    def __init__(self, filetype=None, tmpdir=None):
        self._supported_filetypes = ("csv", "cdf", "nc")
        self.filetype = str() if filetype is None else filetype
        if tmpdir is not None:
            if not os.path.exists(tmpdir):
                raise Exception("tmpdir does not exist")
        if os.name == "nt":
            self._file = tempfile.NamedTemporaryFile(
                prefix="vires_", dir=tmpdir, delete=False)
            self._file.close()
            atexit.register(os.remove, self._file.name)
        else:
            self._file = tempfile.NamedTemporaryFile(
                prefix="vires_", dir=tmpdir)

    def __str__(self):
        return "viresclient ReturnedDataFile object of type " + \
               self.filetype + \
               "\nSave it to a file with .to_file('filename')" + \
               "\nLoad it as a pandas dataframe with .as_dataframe()" + \
               "\nLoad it as an xarray dataset with .as_xarray()"

    def open_cdf(self):
        """Returns the opened file as cdflib.CDF
        """
        return cdflib.CDF(self._file.name)

    def _write_new_data(self, data):
        """Replace the tempfile contents with 'data' (bytes)

        """
        if not isinstance(data, bytes):
            raise TypeError("data must be of type bytes")
        # If on Windows, the file will be closed so needs to be re-opened:
        with open(self._file.name, "wb") as temp_file:
            temp_file.write(data)

    def _write_file(self, filename):
        """Write the tempfile out to a regular file

        """
        with open(self._file.name, "rb") as temp_file:
            with open(filename, 'wb') as out_file:
                shutil.copyfileobj(temp_file, out_file)

    @property
    def filetype(self):
        """Filetype is one of ("csv", "cdf", "nc")
        """
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
        if os.path.isfile(path) and not overwrite:
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

    def to_netcdf(self, path, overwrite=False):
        """Saves the data as a netCDF4 file (this is compatible with HDF5)

        Extension should be .nc

        """
        self._check_outfile(path, 'nc', overwrite)
        # Convert to xarray Dataset
        ds = self.as_xarray()
        ds.to_netcdf(path)
        print("Data written to", path)

    def as_dataframe(self, expand=False):
        """Convert the data to a pandas DataFrame.

        Returns:
            pandas.DataFrame

        """
        if self.filetype == 'csv':
            if expand:
                raise NotImplementedError
            df = make_pandas_DataFrame_from_csv(self._file.name)
        elif self.filetype == 'cdf':
            with FileReader(self._file) as f:
                df = f.as_pandas_dataframe(expand=expand)
        return df

    def as_xarray(self, group=None):
        """Convert the data to an xarray Dataset.

        Note:
            Does not support csv

            Only supports scalar and 3D vectors (currently)

        Returns:
            xarray.Dataset

        """
        if self.filetype == 'csv':
            raise NotImplementedError("csv to xarray is not supported")
        elif self.filetype == 'cdf':
            with FileReader(self._file) as f:
                ds = f.as_xarray_dataset()
        elif self.filetype == 'nc':
            ds = xarray.open_dataset(self._file.name, group=group)
        return ds

    @property
    def sources(self):
        with FileReader(self._file) as f:
            sources = f.sources
        return sources

    @property
    def magnetic_models(self):
        with FileReader(self._file) as f:
            magnetic_models = f.magnetic_models
        return magnetic_models

    @property
    def range_filters(self):
        with FileReader(self._file) as f:
            range_filters = f.range_filters
        return range_filters


class ReturnedData(object):
    """Flexible object for working with data returned from the server

    Holds a list of ReturnedDataFile objects under self.contents

    Example usage::

        ...
        data = request.get_between(..., ...)
        data.sources
        data.range_filters
        data.magnetic_models
        data.as_xarray()
        data.as_dataframe(expand=True)
        data.to_file()

    """

    def __init__(self, filetype=None, N=1, tmpdir=None):
        self.contents = [ReturnedDataFile(filetype=filetype, tmpdir=tmpdir)
                         for i in range(N)]
        # filetype checking / conversion has been done in ReturnedDataFile
        self.filetype = self.contents[0].filetype

    def __str__(self):
        return "viresclient ReturnedData object of type "+self.filetype +\
            "\nSave it to a file with .to_file('filename')" + \
            "\nLoad it as a pandas dataframe with .as_dataframe()" + \
            "\nLoad it as an xarray dataset with .as_xarray()"

    @property
    def filetype(self):
        """Filetype string
        """
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        if not isinstance(value, str):
            raise TypeError("filetype must be a string")
        self._filetype = value

    @property
    def sources(self):
        """ Get list of source product identifiers.
        """
        sources = set()
        for item in self._contents:
            sources.update(item.sources)
        return sorted(sources)

    @property
    def magnetic_models(self):
        """ Get list of magnetic models used.
        """
        models = set()
        for item in self._contents:
            models.update(item.magnetic_models)
        return sorted(models)

    @property
    def range_filters(self):
        """ Get list of filters applied.
        """
        filters = set()
        for item in self._contents:
            filters.update(item.range_filters)
        return sorted(filters)

    @property
    def contents(self):
        """List of ReturnedDataFile objects
        """
        return self._contents

    @contents.setter
    def contents(self, value):
        if not isinstance(value, list):
            raise TypeError("ReturnedData.contents should be a list")
        for i in value:
            if not isinstance(i, ReturnedDataFile):
                raise TypeError(
                    "Items in ReturnedData.contents should be"
                    "of type ReturnedDataFile")
        self._contents = value

    def as_dataframe(self, expand=False):
        """Convert the data to a pandas DataFrame.

        If expand is True, expand some columns, e.g.:

        B_NEC -> B_NEC_N, B_NEC_E, B_NEC_C

        B_VFM -> B_VFM_i, B_VFM_j, B_VFM_k

        Args:
            expand (bool)

        Returns:
            pandas.DataFrame

        """
        return pandas.concat(
            [d.as_dataframe(expand=expand) for d in self.contents])

    def as_xarray(self):
        """Convert the data to an xarray Dataset.

        Returns:
            xarray.Dataset

        """
        # ds_list is a list of xarray.Dataset objects
        #  - they are created from each file in self.contents
        # Some of them may be empty because of the time window they cover
        #  and the filtering that has been applied.
        ds_list = []
        for i, data in enumerate(self.contents):
            ds_part = data.as_xarray()
            if ds_part is None:
                print("Warning: ",
                      "Unable to create dataset from part {} of {}".format(
                        i+1, len(self.contents)),
                      "\n(This part is likely empty)")
            else:
                # Collect the non-empty Datasets
                ds_list.append(ds_part)
        if len(ds_list) == 1:
            ds = ds_list[0]
        else:
            ds_list = [i for i in ds_list if i is not None]
            if ds_list == []:
                return None
            ds = xarray.concat(ds_list, dim="Timestamp")
        # # Test this other option:
        # ds = self.contents[0].as_xarray()
        # for d in self.contents[1:]:
        #     ds = xarray.concat([ds, d.as_xarray()], dim="Timestamp")
        # return ds
        #
        # https://github.com/pydata/xarray/issues/1379
        # concat is slow. Maybe try extracting numpy arrays and rebuilding ds

        # Set the original data sources and models used as metadata
        ds.attrs["Sources"] = self.sources
        ds.attrs["MagneticModels"] = self.magnetic_models
        ds.attrs["RangeFilters"] = self.range_filters
        return ds

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

        .. note::

            This is currently only implemented for smaller data when the
            request has not been split into multiple requests - the limit is
            the equivalent of 50 days of 1Hz measurements. In these situations,
            you can still load the data as pandas/xarray objects (the contents
            of each file is automatically concatenated) and save them as a
            different file type. Or use ``.to_files()`` to save the split data
            directly.

        Args:
            path (str): path to the file to save as
            overwrite (bool): Will overwrite existing file if True

        """
        if len(self.contents) != 1:
            raise NotImplementedError(
                "Data is split into multiple files. Use .to_files instead")
        self.contents[0].to_file(path, overwrite)
