Installation and First Usage
============================

.. note:: For VRE users (it's free! read more: `Swarm <https://notebooks.vires.services>`_, `Aeolus <https://notebooks.aeolus.services>`_), viresclient is already installed and configured so skip these steps

1. Installation
---------------

Python ≥ 3.6 is required. Testing is primarily on Linux, but macOS and Windows should also work. Available through both pip and conda (conda-forge).

.. tabs::

  .. group-tab:: pip

    .. code-block:: sh

      pip install viresclient

  .. group-tab:: conda

    .. code-block:: sh

      conda install --channel conda-forge viresclient

  .. group-tab:: mamba

    .. code-block:: sh

      mamba install --channel conda-forge viresclient

Recommended setup if starting without Python already
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are many ways to work with Python. We recommend using conda/mamba to manage your programming environment because of the availability of many data science packages through conda.

.. tabs::

  .. group-tab:: conda

    1. Install Miniconda: https://docs.conda.io/en/latest/miniconda.html

    2. Set the conda-forge channel as the priority to install packages from::

        conda config --add channels conda-forge
        conda config --set channel_priority strict

    You should do this to avoid mixing packages from the anaconda channel (which can result in broken environments), and try to get all packages from conda-forge where available for consistency.

    3. Create a new conda environment with some recommended packages, including viresclient::

        conda create --name myenv python=3.10 jupyterlab scipy matplotlib pandas xarray cartopy h5py netCDF4 pytables ipywidgets viresclient

    4. Activate the new environment (you do this each time you want to use it)::

        conda activate myenv

  .. group-tab:: mamba

    `Mamba <https://mamba.readthedocs.io/>`_ is a drop-in replacement for conda. You can install it into an existing (base) conda environment (``conda install -c conda-forge mamba``) and then just use ``mamba`` in place of ``conda`` in any commands - mamba is significantly faster. You can also install *mambaforge* directly to get mamba and conda-forge immediately configured in the base environment.

    1. Download and install the `mambaforge installer <https://github.com/conda-forge/miniforge#mambaforge>`_ or check the `mamba documentation <https://mamba.readthedocs.io/en/latest/installation.html>`_

    2. Create a new environment for your development work::

        mamba create --name myenv python=3.10 jupyterlab scipy matplotlib pandas xarray cartopy h5py netCDF4 pytables ipywidgets viresclient

    3. Activate it to use it::

        mamba activate myenv


2. First usage / Configuration
------------------------------

.. tabs::

  .. group-tab:: Swarm

    .. note::

      *For Jupyter notebook users*, just try:

      .. code-block::

        from viresclient import SwarmRequest
        request = SwarmRequest()

      and you will automatically be prompted to set a token.

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

  .. group-tab:: Aeolus

    .. note::

      *For Jupyter notebook users*, just try:

      .. code-block::

        from viresclient import AeolusRequest
        request = AeolusRequest()

      and you will automatically be prompted to set a token.

      A first usage guide is provided as a Jupyter notebook (`view <https://notebooks.aeolus.services/notebooks/02a__intro-aeolus-viresclient>`_). To run the notebook on your computer running Jupyter locally, `right click here to download <https://raw.githubusercontent.com/ESA-VirES/Aeolus-notebooks/main/notebooks/02a__Intro-Aeolus-viresclient.ipynb>`_, or use git to get the whole example repository::

        git clone https://github.com/ESA-VirES/Aeolus-notebooks.git

    Access to the service is through the same user account as on the web interface (https://aeolus.services/) and is enabled through an access token (essentially a password). To get a token, log in to the website and click on your name on the top right to access the settings (`or follow this link <https://aeolus.services/accounts/tokens/>`_). From here, click on "Manage access tokens" and follow the instructions to create a new token.

    To set your token in the client, use either the Python interface:

    .. code-block:: python

      from viresclient import set_token
      set_token("https://aeolus.services/ows")
      # (you will now be prompted to enter the token)

    or the command line tool::

      $ viresclient set_token https://aeolus.services/ows
      Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

      $ viresclient set_default_server https://aeolus.services/ows

    See also: see :doc:`config_details` and :doc:`access_token`


3. Example use
--------------

.. note::

  A brief introduction is given here. For more possibilities, see :doc:`notebook_intro`, and :doc:`capabilities`.

.. tabs::

  .. group-tab:: Swarm

    See also `Swarm access through VirES <https://notebooks.vires.services/notebooks/02a__intro-swarm-viresclient>`_

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

      request.set_products(
        measurements=["F", "B_NEC"],
        models=["MCO_SHA_2C", "MMA_SHA_2C-Primary", "MMA_SHA_2C-Secondary"],
        auxiliaries=["QDLat", "QDLon", "MLT", "OrbitNumber", "SunZenithAngle"],
        residuals=False,
        sampling_step="PT10S"
      )

    Set a parameter range filter to apply. You can add multiple filters in sequence.

    .. code-block:: python

      request.set_range_filter(parameter="Latitude", minimum=0, maximum=90)
      request.set_range_filter("Longitude", 0, 90)

    Specify the time range from which to retrieve data, make the request to the server:

    .. code-block:: python

      data = request.get_between(
        start_time=dt.datetime(2016,1,1),
        end_time=dt.datetime(2016,1,2)
      )

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

  .. group-tab:: Aeolus

    See `Aeolus access through VirES <https://notebooks.aeolus.services/notebooks/02a__intro-aeolus-viresclient>`_
