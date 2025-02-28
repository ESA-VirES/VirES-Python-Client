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

import json
import os
import shutil
import tempfile

import cdflib
import netCDF4
import numpy
import pandas
import xarray

from ._wps import time_util

if os.name == "nt":
    import atexit

from ._data import CONFIG_AEOLUS

CDF_EPOCH_1970 = 62167219200000.0

ALLOWED_SPACECRFTS = ["A", "B", "C", "1", "2", "-"]

# Frame names to use as xarray dimension names
FRAME_NAMES = {
    "NEC": ["B_NEC", "B_OB", "B_CF", "B_SV", "sigma_OB", "sigma_CF", "sigma_SV"],
    "VFM": ["B_VFM", "dB_Sun", "dB_AOCS", "dB_other", "B_error"],
    "quaternion": ["q_NEC_CRF"],
    "WGS84": ["GPS_Position", "LEO_Position"],
    "EEJ_QDLat": ["EEJ"],
    "NE": ["J_NE", "J_CF_NE", "J_DF_NE", "B_NE"],
}
# Reverse mapping of the above
DATANAMES_TO_FRAME_NAMES = {}
for framename, datanameset in FRAME_NAMES.items():
    for dataname in datanameset:
        DATANAMES_TO_FRAME_NAMES[dataname] = framename
# Labels to use for suffixes on expanded columns in pandas dataframe
#   and on dimension coordinates in xarray
FRAME_LABELS = {
    "NEC": ["N", "E", "C"],
    "VFM": ["i", "j", "k"],
    "quaternion": ["1", "i", "j", "k"],
    "WGS84": ["X", "Y", "Z"],
    "EEJ_QDLat": numpy.linspace(-20, 20, 81),
    "NE": ["N", "E"],
}
FRAME_DESCRIPTIONS = {
    "NEC": "NEC frame - North, East, Centre (down)",
    "NE": "Horizontal NE frame - North, East",
    "VFM": "Vector Field Magnetometer instrument frame",
    "EEJ_QDLat": "Quasi-dipole latitude profile between -20 and 20 degrees from the EEF product",
}


class FileReader:
    """Provides access to file contents (wrapper around cdflib)"""

    def __init__(
        self,
        file,
        filetype="cdf",
        time_variable="Timestamp",
        secondary_time_variables=None,
    ):
        """

        Args:
            file (file-like or str)
        """
        if filetype.lower() == "cdf":
            self._cdf = self._open_cdf(file)
            globalatts = self._cdf.globalattsget()
            self.sources = self._ensure_list(
                globalatts.get("ORIGINAL_PRODUCT_NAMES", [])
            )
            self.magnetic_models = self._ensure_list(
                globalatts.get("MAGNETIC_MODELS", [])
            )
            self.data_filters = self._ensure_list(globalatts.get("DATA_FILTERS", []))
            self.variables = self._get_attr_or_key(self._cdf.cdf_info(), "zVariables")
            self._varatts = {var: self._cdf.varattsget(var) for var in self.variables}
            self._varinfo = {var: self._cdf.varinq(var) for var in self.variables}
            self._time_variable = time_variable
            self._secondary_time_variables = (
                secondary_time_variables if secondary_time_variables else []
            )
        else:
            raise NotImplementedError(f"{filetype} not supported")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        try:
            self._cdf.close()
        except AttributeError:
            pass

    @staticmethod
    def _open_cdf(file):
        try:
            f = file.name
        except AttributeError:
            f = file
        try:
            return cdflib.cdfread.CDF(f, string_encoding="utf-8")
        except TypeError:
            return cdflib.cdfread.CDF(f)

    @staticmethod
    def _ensure_list(attribute):
        if isinstance(attribute, str):
            return [attribute]
        else:
            return attribute

    @staticmethod
    def _get_attr_or_key(obj, attr):
        # Used to work around cdflib<1 & >=1 support
        # cdflib>=1 introduces dataclasses in place of some dicts
        if isinstance(obj, dict):
            return obj.get(attr, None)
        else:
            return getattr(obj, attr, None)

    def get_variable(self, var):
        parser = self._get_data_parser(var)
        try:
            data = parser(self._cdf.varget(var))
        except ValueError:
            data = None
        if data is None:
            shape = [0, *self.get_variable_dimsizes(var)]
            data = numpy.empty(shape)
        return data

    def get_variable_units(self, var):
        return self._varatts[var].get("UNITS", "")

    def get_variable_description(self, var):
        desc = self._varatts[var].get("DESCRIPTION", "")
        catdesc = self._varatts[var].get("CATDESC", "")
        return desc if desc else catdesc

    def get_variable_numdims(self, var):
        return self._get_attr_or_key(self._varinfo[var], "Num_Dims")

    def get_variable_dimsizes(self, var):
        return self._get_attr_or_key(self._varinfo[var], "Dim_Sizes")

    @staticmethod
    def _cdftime_to_datetime(t):
        try:
            return pandas.to_datetime((t - CDF_EPOCH_1970) / 1e3, unit="s")
        except TypeError:
            return []

    def _get_data_parser(self, var):
        def default_parser(data):
            return data

        def time_parser(data):
            return self._cdftime_to_datetime(data)

        if var == self._time_variable or var in self._secondary_time_variables:
            return time_parser
        else:
            return default_parser

    def as_pandas_dataframe(self, expand=False):
        # Use the variables in the file as columns to create in the dataframe.
        # Skip Timestamp as it will be used as the index.
        columns = set(self.variables)
        columns.remove(self._time_variable)
        # Split columns according to those to be expanded into multiple columns
        if expand:
            columns_to_expand = {
                c
                for c in columns
                if c in DATANAMES_TO_FRAME_NAMES.keys() or "B_NEC" in c
            }
            # Avoid conflict with 2D AOB_FAC Quality variable
            # when accessing AUX_OBS Quality
            if any(["AUX_OBS" in s for s in self.sources]):
                columns_to_expand.discard("Quality")
        else:
            columns_to_expand = set()
        columns_standard = columns.difference(columns_to_expand)
        # Initialise dataframe with Timestamp as index
        df = pandas.DataFrame(index=self.get_variable(self._time_variable))
        df.index.name = self._time_variable
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
        # Separately add non-expanded and expanded columns
        for column in columns_standard:
            df[column] = list(self.get_variable(column))
        for column in columns_to_expand:
            vector_data = self.get_variable(column)
            framename = DATANAMES_TO_FRAME_NAMES.get(column, "NEC")
            suffixes = FRAME_LABELS[framename]
            if len(vector_data.shape) > 2:
                raise NotImplementedError(f"{column}")
            if vector_data.shape[1] != len(suffixes):
                raise NotImplementedError(f"{column}")
            for i, suffix in enumerate(suffixes):
                df[column + "_" + str(suffix)] = vector_data[:, i]
        return df

    def as_xarray_dataset(self, reshape=False):
        # NB currrently does not set the global metadata (attrs)
        #  (avoids issues with concatenating them)
        #  (this is done in ReturnedData)
        # Initialise dataset with time coordinate
        ds = xarray.Dataset(
            coords={self._time_variable: self.get_variable(self._time_variable)}
        )
        # Add Spacecraft variable as Categorical to save memory
        if "Spacecraft" in self.variables:
            ds["Spacecraft"] = (
                (self._time_variable,),
                pandas.Categorical(
                    self.get_variable("Spacecraft"), categories=ALLOWED_SPACECRFTS
                ),
            )
        datanames = set(self.variables) - {self._time_variable, "Spacecraft"}
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
                ds[dataname] = ((self._time_variable,), data)
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
                ds[dataname] = (
                    (self._time_variable, dimname),
                    self.get_variable(dataname),
                )
            # 3D case (matrix series), e.g. QDBasis
            elif numdims == 2:
                dimname1 = "%s_dim1" % dataname
                dimname2 = "%s_dim2" % dataname
                ds[dataname] = (
                    (self._time_variable, dimname1, dimname2),
                    self.get_variable(dataname),
                )
            else:
                raise NotImplementedError("%s: array too complicated" % dataname)
        # Add named coordinates
        for dimname, dimlabels in FRAME_LABELS.items():
            if dimname in dims_used:
                ds[dimname] = numpy.array(dimlabels)
                ds = ds.set_coords(dimname)
        #         ds[dimname].attrs["description"] = FRAME_DESCRIPTIONS.get(
        #             dimname, None)
        #         ds = ds.set_coords(dimname)
        # Reshape to a sensible higher dimensional structure
        # Currently only for GVO data, and without magnetic model values or auxiliaries
        # Inefficient as it is duplicating the data (ds -> ds2)
        if reshape:
            ds = self.reshape_dataset(ds)
        # Add metadata of each variable
        for var in list(ds.data_vars) + list(ds.coords):
            try:
                ds[var].attrs["units"] = self.get_variable_units(var)
            except KeyError:
                ds[var].attrs["units"] = ""
            try:
                ds[var].attrs["description"] = self.get_variable_description(var)
            except KeyError:
                ds[var].attrs["description"] = FRAME_DESCRIPTIONS.get(var, "")
        # Remove unused Timestamp unit (-)
        # for xarray 0.17 compatibility when writing to netcdf
        ds[self._time_variable].attrs.pop("units", None)
        return ds

    def reshape_dataset(self, ds):
        if "SiteCode" in ds.data_vars:
            codevar = "SiteCode"
        elif "IAGA_code" in ds.data_vars:
            codevar = "IAGA_code"
        else:
            raise NotImplementedError(
                """
                Only available for GVO dataset where the "SiteCode"
                parameter has been requested, or OBS dataset with "IAGA_code"
                """
            )
        # Create integer "Site" identifier based on SiteCode / IAGA_code
        sites = dict(enumerate(sorted(set(ds[codevar].values))))
        sites_inv = {v: k for k, v in sites.items()}
        if len(sites) == 0:
            _ds_locs = ds
        else:
            # Identify (V)OBS locations and mapping from integer "Site" identifier
            pos_vars = ["Longitude", "Latitude", "Radius", codevar]
            _ds_locs = next(iter(ds[pos_vars].groupby(self._time_variable)))[1]
            if len(sites) > 1:
                _ds_locs = _ds_locs.drop(self._time_variable).rename(
                    {self._time_variable: "Site"}
                )
            else:
                _ds_locs = _ds_locs.drop(self._time_variable).expand_dims("Site")
            _ds_locs["Site"] = [
                sites_inv.get(code) for code in _ds_locs[codevar].values
            ]
            _ds_locs = _ds_locs.sortby("Site")
        # Create dataset initialised with the (V)OBS positional info as coords
        # and datavars (empty) reshaped to (Site, Timestamp, ...)
        t = numpy.unique(ds[self._time_variable])
        ds2 = xarray.Dataset(
            coords={
                self._time_variable: t,
                codevar: (("Site"), _ds_locs[codevar].data),
                "Latitude": ("Site", _ds_locs["Latitude"].data),
                "Longitude": ("Site", _ds_locs["Longitude"].data),
                "Radius": ("Site", _ds_locs["Radius"].data),
                "NEC": ["N", "E", "C"],
            },
        )
        # (Dropping unused Spacecraft var)
        data_vars = set(ds.data_vars) - {
            "Latitude",
            "Longitude",
            "Radius",
            codevar,
            "Spacecraft",
        }
        N_sites = len(_ds_locs[codevar])
        # Create empty data variables to be infilled
        for var in data_vars:
            shape = [N_sites, len(t), *ds[var].shape[1:]]
            ds2[var] = ("Site", *ds[var].dims), numpy.empty(shape, dtype=ds[var].dtype)
            ds2[var][...] = None
        # Loop through each (V)OBS site to infill the data
        if N_sites != 0:
            for k, _ds in dict(ds.groupby(codevar)).items():
                site = sites_inv.get(k)
                for var in data_vars:
                    ds2[var][site, ...] = _ds[var].values
        # Revert to using only the "SiteCode"/"IAGA_code" identifier
        ds2 = ds2.set_index({"Site": codevar})
        ds2 = ds2.rename({"Site": codevar})
        return ds2


def make_pandas_DataFrame_from_csv(csv_filename, time_variable="Timestamp"):
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
    df[time_variable] = df[time_variable].apply(time_util.parse_datetime)
    # Convert the columns of vectors from strings to lists
    # Returns empty dataframe when retrieval from server is empty
    if len(df) != 0:
        # Convert the columns of vectors from strings to lists
        for col in df:
            if type(df[col][0]) is str:
                if df[col][0][0] == "{":
                    df[col] = df[col].apply(
                        lambda x: [float(y) for y in x.strip("{}").split(";")]
                    )
    df.set_index(time_variable, inplace=True)
    return df


class ReturnedDataFile:
    """For handling individual files returned from the server.

    Holds the data returned from the server and the data type.
    Data is held in a NamedTemporaryFile, which is automatically closed and
    destroyed when it goes out of scope.
    Provides output to different file types and data objects.

    """

    def __init__(self, filetype=None, tmpdir=None, file_options=None):
        self._file_options = file_options or {}
        self._supported_filetypes = ("csv", "cdf", "nc")
        self.filetype = "" if filetype is None else filetype
        if tmpdir is not None:
            if not os.path.exists(tmpdir):
                raise Exception("tmpdir does not exist")
        if os.name == "nt":
            self._file = tempfile.NamedTemporaryFile(
                prefix="vires_", dir=tmpdir, delete=False
            )
            self._file.close()
            atexit.register(os.remove, self._file.name)
        else:
            self._file = tempfile.NamedTemporaryFile(prefix="vires_", dir=tmpdir)

    def __str__(self):
        return (
            "viresclient ReturnedDataFile object of type "
            + self.filetype
            + "\nSave it to a file with .to_file('filename')"
            + "\nLoad it as a pandas dataframe with .as_dataframe()"
            + "\nLoad it as an xarray dataset with .as_xarray()"
        )

    def open_cdf(self):
        """Returns the opened file as cdflib.CDF"""
        return FileReader._open_cdf(self._file.name)

    def _write_new_data(self, data):
        """Replace the tempfile contents with 'data' (bytes)"""
        if not isinstance(data, bytes):
            raise TypeError("data must be of type bytes")
        # If on Windows, the file will be closed so needs to be re-opened:
        with open(self._file.name, "wb") as temp_file:
            temp_file.write(data)

    def _write_file(self, filename):
        """Write the tempfile out to a regular file"""
        with open(self._file.name, "rb") as temp_file:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(temp_file, out_file)

    @property
    def filetype(self):
        """Filetype is one of ("csv", "cdf", "nc")"""
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        if not isinstance(value, str):
            raise TypeError("filetype must be a string")
        value = value.lower()
        if value not in self._supported_filetypes:
            raise TypeError(
                f"Chosen filetype must be one of: {self._supported_filetypes}"
            )
        self._filetype = value

    @staticmethod
    def _check_outfile(path, path_extension, overwrite=False):
        """Check validity of path and extension, and if it exists already"""
        if not isinstance(path, str):
            raise TypeError("path must be a string")
        if path.split(".")[-1].lower() != path_extension:
            raise TypeError(f"Filename extension should be {path_extension}")
        if os.path.isfile(path) and not overwrite:
            raise FileExistsError(
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
        self._check_outfile(path, "nc", overwrite)
        # Convert to xarray Dataset
        ds = self.as_xarray()
        ds.to_netcdf(path)
        print("Data written to", path)

    def as_dataframe(self, expand=False):
        """Convert the data to a pandas DataFrame.

        Returns:
            pandas.DataFrame

        """
        if self.filetype == "csv":
            if expand:
                raise NotImplementedError
            df = make_pandas_DataFrame_from_csv(self._file.name)
        elif self.filetype == "nc":
            df = self.as_xarray().to_dataframe()
        elif self.filetype == "cdf":
            with FileReader(self._file, **self._file_options) as f:
                df = f.as_pandas_dataframe(expand=expand)
        return df

    def as_xarray(self, group=None, reshape=False):
        """Convert the data to an xarray Dataset.

        Note:
            Does not support csv

            Only supports scalar and 3D vectors (currently)

        Returns:
            xarray.Dataset

        """
        if self.filetype == "csv":
            raise NotImplementedError("csv to xarray is not supported")
        elif self.filetype == "cdf":
            with FileReader(self._file, **self._file_options) as f:
                ds = f.as_xarray_dataset(reshape=reshape)
        elif self.filetype == "nc":
            # xarrays open_dataset does not retrieve data in groups
            # group needs to be specified while opening
            # we iterate here over the available groups
            # TODO: what happens with groups of different sizes and attributes
            nc = netCDF4.Dataset(self._file.name)
            ds = xarray.Dataset()

            # some datasets do not have groups
            if nc.groups:
                for group in nc.groups:
                    ds = ds.merge(
                        xarray.open_dataset(
                            self._file.name, group=group, engine="netcdf4"
                        )
                    )
            else:
                ds = xarray.open_dataset(self._file.name, engine="netcdf4")
            # Go through Aeolus parameters and check if unit information is available
            # TODO: We are "flattening" the list of parameters, same parameter
            # id in different collection types could select incorrect one
            for parameter in ds:
                for coll_obj in CONFIG_AEOLUS["collections"].values():
                    for field_type in coll_obj.values():
                        if parameter in field_type and field_type[parameter]["uom"]:
                            ds[parameter].attrs["units"] = field_type[parameter]["uom"]
            # TODO: Go through Swarm parameters
        return ds

    def as_xarray_dict(self):
        """Convert the data to an xarray Dataset.

        Note:
            Only supports netCDF format

        Returns:
            dict of xarray.Dataset

        """
        if self.filetype == "csv":
            raise NotImplementedError("csv to xarray dict is not supported")
        elif self.filetype == "cdf":
            raise NotImplementedError("cdf to xarray dict is not supported")
        elif self.filetype == "nc":
            result_dict = {}
            nc = netCDF4.Dataset(self._file.name)
            # some datasets do not have groups
            if nc.groups:
                for group in nc.groups:
                    ds = xarray.Dataset()
                    ds = ds.merge(
                        xarray.open_dataset(
                            self._file.name, group=group, engine="netcdf4"
                        )
                    )
                    for parameter in ds:
                        for coll_obj in CONFIG_AEOLUS["collections"].values():
                            for field_type in coll_obj.values():
                                if (
                                    parameter in field_type
                                    and field_type[parameter]["uom"]
                                ):
                                    ds[parameter].attrs["units"] = field_type[
                                        parameter
                                    ]["uom"]
                    result_dict[group] = ds
            else:
                result_dict["group"] = xarray.open_dataset(
                    self._file.name, engine="netcdf4"
                )

        return result_dict

    @property
    def sources(self):
        if self.filetype == "nc":
            nc = netCDF4.Dataset(self._file.name)
            json_hist = json.loads(nc.history)
            sources = [
                elem
                for elem in zip(
                    json_hist["inputFiles"],
                    json_hist["baselines"],
                    json_hist["software_vers"],
                )
            ]
        else:
            with FileReader(self._file, **self._file_options) as f:
                sources = f.sources
        return sources

    @property
    def magnetic_models(self):
        with FileReader(self._file, **self._file_options) as f:
            magnetic_models = f.magnetic_models
        return magnetic_models

    @property
    def data_filters(self):
        with FileReader(self._file, **self._file_options) as f:
            data_filters = f.data_filters
        return data_filters


class ReturnedData:
    """Flexible object for working with data returned from the server

    Holds a list of ReturnedDataFile objects under self.contents

    Example usage::

        ...
        data = request.get_between(..., ...)
        data.sources
        data.data_filters
        data.magnetic_models
        data.as_xarray()
        data.as_xarray_dict()
        data.as_dataframe(expand=True)
        data.to_file()

    """

    def __init__(self, filetype=None, N=1, tmpdir=None, file_options=None):
        self._time_variable = (file_options or {}).get("time_variable", "Timestamp")

        self.contents = [
            ReturnedDataFile(
                filetype=filetype,
                tmpdir=tmpdir,
                file_options=file_options,
            )
            for i in range(N)
        ]
        # filetype checking / conversion has been done in ReturnedDataFile
        self.filetype = self.contents[0].filetype

    def __str__(self):
        return (
            "viresclient ReturnedData object of type "
            + self.filetype
            + "\nSave it to a file with .to_file('filename')"
            + "\nLoad it as a pandas dataframe with .as_dataframe()"
            + "\nLoad it as an xarray dataset with .as_xarray()"
        )

    @property
    def filetype(self):
        """Filetype string"""
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        if not isinstance(value, str):
            raise TypeError("filetype must be a string")
        self._filetype = value

    @property
    def sources(self):
        """Get list of source product identifiers."""
        sources = set()
        for item in self._contents:
            sources.update(item.sources)
        return sorted(sources)

    @property
    def magnetic_models(self):
        """Get list of magnetic models used."""
        models = set()
        for item in self._contents:
            models.update(item.magnetic_models)
        return sorted(models)

    @property
    def data_filters(self):
        """Get list of filters applied."""
        filters = set()
        for item in self._contents:
            filters.update(item.data_filters)
        return sorted(filters)

    @property
    def contents(self):
        """List of ReturnedDataFile objects"""
        return self._contents

    @contents.setter
    def contents(self, value):
        if not isinstance(value, list):
            raise TypeError("ReturnedData.contents should be a list")
        for i in value:
            if not isinstance(i, ReturnedDataFile):
                raise TypeError(
                    "Items in ReturnedData.contents should be"
                    "of type ReturnedDataFile"
                )
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
        dataframes = [data.as_dataframe(expand=expand) for data in self.contents]
        if len(dataframes) > 1:
            return pandas.concat([df for df in dataframes if not df.empty])
        else:
            return dataframes[0]

    def as_xarray(self, reshape=False):
        """Convert the data to an xarray Dataset.

        Args:
            reshape (bool): Reshape to a convenient higher dimensional form

        Returns:
            xarray.Dataset

        """
        # ds_list is a list of xarray.Dataset objects
        #  - they are created from each file in self.contents
        # Some of them may be empty because of the time window they cover
        #  and the filtering that has been applied.
        ds_list = []
        for i, data in enumerate(self.contents):
            ds_part = data.as_xarray(reshape=reshape)
            if ds_part is None:
                print(
                    "Warning: ",
                    "Unable to create dataset from part {} of {}".format(
                        i + 1, len(self.contents)
                    ),
                    "\n(This part is likely empty)",
                )
            else:
                ds_list.append(ds_part)
        ds_list = [i for i in ds_list if i is not None]

        if ds_list == []:
            return None
        elif len(ds_list) == 1:
            ds = ds_list[0]
        elif self._time_variable in ds_list[0].dims:
            # Address simpler concatenation case for VirES for Swarm
            # Timestamp always exists for Swarm, but is not present in Aeolus
            # Remove datasets of length 0 so that concatenation works
            ds_list = [ds for ds in ds_list if ds[self._time_variable].size != 0]
            ds = xarray.concat(ds_list, dim=self._time_variable)
        else:
            # Address complex concatenation case for VirES for Aeolus
            dims = [d for d in list(ds_list[0].dims) if "array" not in d]
            if dims == []:
                return None
            elif len(dims) == 1:
                ds = xarray.concat(ds_list, dim=dims[0])
            else:
                ds_list_per_dim = []
                for d in dims:
                    drop_dims = [dd for dd in dims if dd != d]
                    ds_list_per_dim.append(
                        xarray.concat(
                            [_ds.drop_dims(drop_dims) for _ds in ds_list], dim=d
                        )
                    )
                ds = xarray.merge(ds_list_per_dim)

        # Set the original data sources and models used as metadata
        # only for cdf data types
        ds.attrs["Sources"] = self.sources
        if self.filetype == "cdf":
            ds.attrs["MagneticModels"] = self.magnetic_models
            ds.attrs["AppliedFilters"] = self.data_filters
        return ds

    def as_xarray_dict(self):
        """Convert the data to a dict containing an xarray per group.

        Returns:
            dict of xarray.Dataset

        """
        # ds_list is a list of xarray.Dataset objects
        #  - they are created from each file in self.contents
        # Some of them may be empty because of the time window they cover
        #  and the filtering that has been applied.
        ds_list = []
        for i, data in enumerate(self.contents):
            ds_part = data.as_xarray_dict()
            if ds_part is None:
                print(
                    "Warning: ",
                    "Unable to create dataset from part {} of {}".format(
                        i + 1, len(self.contents)
                    ),
                    "\n(This part is likely empty)",
                )
            else:
                ds_list.append(ds_part)
        ds_list = [i for i in ds_list if i is not None]
        if ds_list == []:
            return None
        elif len(ds_list) == 1:
            # add sources to all dict as_xarray
            for xa_ds in ds_list[0].values():
                xa_ds.attrs["Sources"] = self.sources
            ds_dict = ds_list[0]
        else:
            ds_dict = {}
            ds_list = [i for i in ds_list if i is not None]
            if ds_list == []:
                return None
            for group in ds_list[0]:
                group_list = [g[group] for g in ds_list if g is not None]
                ds_dict[group] = xarray.merge(group_list)
                ds_dict[group].attrs["Sources"] = self.sources
        return ds_dict

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
            raise Exception(f"Number of paths must equal number of files ({nfiles})")
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
                "Data is split into multiple files. Use .to_files instead"
            )
        self.contents[0].to_file(path, overwrite)
