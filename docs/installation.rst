Installation and First Usage
============================

.. note:: For VRE users (it's free! read more: `Swarm <https://notebooks.vires.services>`_, `Aeolus <https://notebooks.aeolus.services>`_), viresclient is already installed and configured so skip these steps

1. Installation
---------------

Python ≥ 3.6 is required. Testing is primarily on Linux, but macOS and Windows should also work.

It can currently be installed with::

  pip install viresclient

Dependencies::

  requests
  Jinja2
  tables
  tqdm
  cdflib
  pandas
  xarray
  netCDF4

pip will fetch these automatically - if you are using conda, it may be better to install these first using conda instead (where available)::

    conda install requests jinja2 pytables tqdm pandas xarray netcdf4
    pip install viresclient

Recommended setup if starting without Python already
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install Miniconda: https://docs.conda.io/en/latest/miniconda.html
2. Create a new conda environment with some recommended packages::

    conda create --name myenv scipy matplotlib pandas xarray cartopy jupyter jupyterlab flake8 dask h5py netCDF4 jinja2 pytables tqdm ipywidgets

  Activate the new environment (you do this each time you want to use it)::

    conda activate myenv

3. Use pip to install viresclient::

    pip install viresclient



2. First usage / Configuration
------------------------------

.. note:: For Jupyter notebook users:

  On creation of a SwarmRequest object, you will automatically be prompted to set a token. Just try::

    from viresclient import SwarmRequest
    request = SwarmRequest()

  and follow the instructions.

  A first usage guide is provided as a Jupyter notebook (`view <https://notebooks.vires.services/notebooks/02a__intro-swarm-viresclient>`_). To run the notebook on your computer running Jupyter locally, `right click here to download <https://raw.githubusercontent.com/Swarm-DISC/Swarm_notebooks/master/notebooks/02a__Intro-Swarm-viresclient.ipynb>`_, or use git to get the whole example repository::

    git clone https://github.com/Swarm-DISC/Swarm_notebooks.git

Access to the service is through the same user account as on the web interface (https://vires.services/) and is enabled through an access token (essentially a password). To get a token, log in to the website and click on your name on the top right to access the settings (`or follow this link <https://vires.services/accounts/tokens/>`_). From here, click on "Manage access tokens" and follow the instructions to create a new token.

To set your token in the client, use either the Python interface:

.. code-block:: python

  from viresclient import set_token
  set_token("https://vires.services/ows")
  # (you will now be prompted to enter the token)

or the command line tool::

  $ viresclient set_token https://vires.services/ows
  Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

  $ viresclient set_default_server https://vires.services/ows

See also: see :doc:`config_details` and :doc:`access_token`

3. Example use
--------------

.. note::

  A brief introduction is given here. For more possibilities, see :doc:`notebook_intro`

Choose which collection to access (see :doc:`available_parameters` for more options):

.. code-block:: python

  import datetime as dt
  from viresclient import SwarmRequest

  request = SwarmRequest()
  request.set_collection("SW_OPER_MAGA_LR_1B")

Next, use ``.set_products()`` to choose a combination of variables to retrieve, specified by keywords.

- ``measurements`` are measured by the satellite and members of the specified ``collection``
- ``models`` are evaluated on the server at the positions of the satellite
- ``auxiliaries`` are additional parameters not unique to the ``collection``
- if ``residuals`` is set to ``True`` then only data-model residuals are returned
- optionally use ``sampling_step`` to specify a resampling of the original time series (an `ISO-8601 duration <https://en.wikipedia.org/wiki/ISO_8601#Durations>`_).

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

Specify the time range from which to retrieve data, make the request to the server:

.. code-block:: python

  data = request.get_between(start_time=dt.datetime(2016,1,1),
                             end_time=dt.datetime(2016,1,2))

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
