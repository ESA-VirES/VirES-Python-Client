Installation and first usage
============================

1. Installation
---------------

.. note:: For VRE (Virtual Research Environment) users:

  viresclient is already installed so skip this step. Log in at https://vre.vires.services/ and refer to documentation at https://swarm-vre.readthedocs.io/

  You will still need to configure viresclient (see step 2)

Python ≥ 3.5 is required. Tested primarily on Linux, but macOS and Windows should also work (on v0.4+).

It can currently be installed with::

  pip install viresclient

Dependencies::

  Jinja2 ≥ 2.10.0
  tables ≥ 3.4.4
  tqdm   ≥ 4.23.0
  cdflib ≥ 0.3.9
  pandas ≥ 0.18.0
  xarray ≥ 0.11.0

(pip will fetch these automatically - if you are using conda, it may be better to install these first using conda instead::

    conda install jinja2 pytables tqdm pandas xarray
    pip install viresclient

Recommended setup if starting without Python already
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install Miniconda for Python 3.7: https://docs.conda.io/en/latest/miniconda.html
2. Create a new conda environment with some recommended packages::

    conda create --name py37 scipy matplotlib pandas xarray cartopy jupyter jupyterlab flake8 dask h5py netCDF4 jinja2 pytables tqdm

  Activate the new environment (you do this each time you want to use it)::

    conda activate py37

3. Use pip to install viresclient::

    pip install viresclient



2. First usage / Configuration
------------------------------

.. note:: For Jupyter notebook users:

  The instructions for first time usage are also provided as a Jupyter notebook which you might find easier to use. Download the notebook to your environment and follow the instructions.

  https://github.com/smithara/viresclient_examples/blob/master/0_first_usage.ipynb

  To download the whole example repository, open a terminal and do::

    git clone https://github.com/smithara/viresclient_examples.git

  then launch the notebook, ``viresclient_examples/0_first_usage.ipynb``

Access to the service is through the same user account as on the web interface (https://vires.services/) and is enabled through a token. To get a token, log in to the website and click on your name on the top right to access the settings. From here, click on "Manage access tokens" and follow the instructions to create a new token.

While it is possible to enter the server URL and access credentials each time a new request object is created

.. code-block:: python

  from viresclient import SwarmRequest

  # both URL and access token passed as request object's parameters
  request = SwarmRequest(
      url="https://vires.services/ows",
      token="r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-"
  )

it is more convenient to omit them from the code and store them in a private configuration file

.. code-block:: python

  # access token read from configuration
  request = SwarmRequest(url="https://vires.services/ows")

  # both default URL and access token read from configuration
  request = SwarmRequest()

The server access configuration can be set either by command line interface (CLI), Python code, or editing of the configuration file, as described in the following sections.

Configuration via CLI
^^^^^^^^^^^^^^^^^^^^^

The ``viresclient`` shell command can be used to set the server access configuration::

  $ viresclient set_token https://vires.services/ows
  Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

  $ viresclient set_default_server https://vires.services/ows

Configuration via Python
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code to store the token in the ``viresclient`` configuration

.. code-block:: python

  from viresclient import ClientConfig

  cc = ClientConfig()
  cc.set_site_config("https://vires.services/ows", token="r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-")
  cc.default_url = "https://vires.services/ows"
  cc.save()


Configuration File
^^^^^^^^^^^^^^^^^^

The client configuration is saved as a text file at ``~/.viresclient.ini``.  This configuration file can edited in a text editor::

  [https://vires.services/ows]
  token = r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

  [default]
  url = https://vires.services/ows

When creating the configuration file manually make sure the file is readable by its owner only::

  $ chmod 0600 ~/.viresclient.ini
  $ ls -l ~/.viresclient.ini
  -rw-------  1 owner owner  361 May 12 09:12 /home/owner/.viresclient.ini


.. note:: For DISC users / developers:

  The user account for the DISC server is separate. A token can be generated in the same way and stored in the configuration alongside the token for other site::

    $ viresclient set_token https://vires.services/ows
    Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

    $ viresclient set_token https://staging.viresdisc.vires.services/ows
    Enter access token: VymMHhWjZ-9nSVs-FuPC27ca8C6cOyij

    $ viresclient set_default_server https://vires.services/ows

  Using ``SwarmRequest()`` without the URL parameter will use the default URL set above. To access a non-default server the URL parameter must be used:

  .. code-block:: python

    from viresclient import SwarmRequest

    # request using the default server (https://vires.services/ows)
    request = SwarmRequest()

    # request to an alternative, non-default server
    request = SwarmRequest(url="https://staging.viresdisc.vires.services/ows")


3. Example use
--------------

.. note::

  A brief introduction is given here. For more possibilities, see :doc:`notebook_intro`

Choose which collection to access (see :doc:`available_parameters` for more options):

.. code-block:: python

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
