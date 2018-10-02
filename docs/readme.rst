Introduction
============

This is the documentation for the ``viresclient`` Python package. This is a tool which connects to a VirES_ server through the WPS_ interface and handles product requests and downloads.

.. _VirES: https://vires.services
.. _WPS: http://www.opengeospatial.org/standards/wps

Data can be accessed from the server as CSV or CDF files and saved to disk, or loaded directly into Python objects pandas.DataFrame_, or xarray.Dataset_.

.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe

.. _xarray.Dataset: http://xarray.pydata.org/en/stable/data-structures.html#dataset

cdflib_ is used to read CDF files.

.. _cdflib: https://github.com/MAVENSDC/cdflib

The project is on GitHub at https://github.com/ESA-VirES/VirES-Python-Client - please feel free to contribute with any code/suggestions/comments.

A repository of example notebooks can be found at https://github.com/smithara/viresclient_examples. We welcome contribution of notebooks to this repository that show some short analyses or generating useful figures.

Installation
------------

Python ≥ 3.5 is required for full support (since cdflib requires ≥ 3.5).

Python 3.4 can also be used, but conversion from CDF to pandas/xarray is not supported - you can still download and save CDF files - :meth:`viresclient.ReturnedData.to_file`, or download as CSV files and convert to pandas - :meth:`viresclient.ReturnedData.as_dataframe`. (Partial?) support for 2.7 and 3.4 could be added in the future, but their usage is not recommended (https://python3statement.org/).

It can currently be installed with::

  pip install viresclient

Dependencies::

  Jinja2
  pandas
  cdflib
  tables
  tqdm
  xarray

Example usage
-------------

Import the package and set up the connection to the server:

.. code-block:: python

  from viresclient import SwarmRequest
  import datetime as dt

  request = SwarmRequest(url="https://staging.viresdisc.vires.services/openows",
                         username="your username",
                         password="your password")

Choose which collection to access:

.. code-block:: python

  request.set_collection("SW_OPER_MAGA_LR_1B")

Choose a combination of variables to retrieve. ``measurements`` are measured by the satellite and members of the specified ``collection``; ``models`` are evaluated on the server at the positions of the satellite; ``auxiliaries`` are additional parameters not unique to the ``collection``. If ``residuals`` is set to ``True`` then only data-model residuals are returned. Optionally specify a resampling of the original time series with ``sampling_step`` (an `ISO-8601 duration <https://en.wikipedia.org/wiki/ISO_8601#Durations>`_).

.. code-block:: python

  request.set_products(measurements=["F","B_NEC"],
                       models=["MCO_SHA_2C", "MMA_SHA_2C-Primary", "MMA_SHA_2C-Secondary"],
                       auxiliaries=["QDLat", "QDLon", "MLT", "OrbitNumber", "SunZenithAngle"],
                       residuals=False,
                       sampling_step="PT10S")

Set a parameter range filter to apply. You can add multiple filters in sequence

.. code-block:: python

  request.set_range_filter(parameter="Latitude",
                           minimum=0,
                           maximum=90)

  request.set_range_filter("Longitude", 0, 90)

Specify the time range from which to retrieve data, make the request to the server (specifying the output file format, currently either csv or cdf):

.. code-block:: python

  data = request.get_between(start_time=dt.datetime(2016,1,1),
                             end_time=dt.datetime(2016,1,2),
                             filetype="cdf",
                             asynchronous=True)

Transfer your data to a pandas.DataFrame_, or a xarray.Dataset_, or just save it as is:

.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe

.. _xarray.Dataset: http://xarray.pydata.org/en/stable/data-structures.html#dataset

.. code-block:: python

  df = data.as_dataframe()
  ds = data.as_xarray()
  data.to_file('outfile.cdf', overwrite=False)

The returned data has columns for:
 - ``Spacecraft, Timestamp, Latitude, Longitude, Radius``
 - those specified by ``measurements`` and ``auxiliaries``
... and model values and residuals, named as:
   - ``F_<model_id>``           -- scalar field
   - ``B_NEC_<model_id>``       -- vector field
   - ``F_res_<model_id>``       -- scalar field residual (``F - F_<model_id>``)
   - ``B_NEC_res_<model_id>``   -- vector field residual (``B_NEC - B_NEC_<model_id>``)
