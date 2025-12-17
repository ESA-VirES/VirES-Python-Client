Installation and First Usage
============================

.. note:: For VRE users (it's free! read more: `Swarm <https://notebooks.vires.services>`_, `Aeolus <https://notebooks.aeolus.services>`_), viresclient is already installed and configured so skip these steps

1. Installation and updating
----------------------------

The package is available through both pip (PyPI) and conda (conda-forge). To add viresclient to an existing environment, use your preferred tool:

.. tabs::

  .. group-tab:: pip

    To install:

    .. code-block:: sh

      python -m pip install viresclient

    To update:

    .. code-block:: sh

      python -m pip install --upgrade viresclient

    .. tip::

      If you are using an online notebook (e.g. Jupyter, Google Colab), you can run (in a notebook cell):

      .. code-block:: sh

        %pip install --upgrade viresclient

  .. group-tab:: uv

    To install:

    (Assuming you use a `uv project <https://docs.astral.sh/uv/guides/projects/>`_)

    .. code-block:: sh

      uv add viresclient

    To update:

    .. code-block:: sh

      uv lock --upgrade-package viresclient

  .. group-tab:: conda

    To install:

    .. code-block:: sh

      conda install --channel conda-forge viresclient

    To update:

    .. code-block:: sh

      conda update --channel conda-forge viresclient

  .. group-tab:: mamba

    To install:

    .. code-block:: sh

      mamba install --channel conda-forge viresclient

    To update:

    .. code-block:: sh

      mamba update --channel conda-forge viresclient


Recommended setup if starting without Python already
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are many ways to work with Python. Depending on your computing environment, we recommend using either:

- `uv <https://docs.astral.sh/uv/>`_: if your project relies specifically on Python packages (available via `PyPI <https://pypi.org/>`_) and you can use a system package manager (e.g. apt) to manage non-Python dependencies
- `Mamba <https://mamba.readthedocs.io/>`_ or `conda <https://docs.conda.io/projects/conda/>`_: which also manage non-Python dependencies (from `conda-forge <https://conda-forge.org/>`_)

  - Use mamba preferably. It is a drop-in replacement for conda and is separate from Anaconda Inc.
  - Use conda if you have an existing Anaconda or Miniconda installation
- `Pixi <https://pixi.sh/>`_: a newer tool that provides reproducible environments with lock files; works with both conda and pip packages (integrates with uv)

This guidance is appropriate for unix-like platforms (macOS & Linux & WSL). If you are using Windows, we recommend using `Windows Subsystem for Linux (WSL) <https://learn.microsoft.com/en-us/windows/wsl/>`_. While viresclient is compatible with Windows, you will get a more consistent experience with the scientific Python ecosystem by using WSL.

.. tabs::

  .. group-tab:: uv

    1. `Install uv <https://docs.astral.sh/uv/getting-started/installation>`_
    2. Create a new `project <https://docs.astral.sh/uv/guides/projects/>`_::

        uv init --python 3.12 my-science-project

    3. Enter the project and add some packages (including viresclient)::

        cd my-science-project
        uv add viresclient scipy matplotlib cartopy

    4. Run code within the uv-managed environment. Either:

       - Use `uv run <https://docs.astral.sh/uv/guides/scripts/>`_ to run scripts
       - Activate the environment manually (``source .venv/bin/activate``)
       - Configure your IDE to use this environment
       - `Launch JupyterLab together with your project's dependencies <https://docs.astral.sh/uv/guides/integration/jupyter/>`_::

          cd my-science-project
          uv run --with jupyter jupyter lab

    You should avoid using pip to install or update packages. By instead using ``uv add <package>``, or ``uv lock --upgrade-package <package>``, this lets uv track your project's dependencies (via the ``pyproject.toml`` file) and the exact versions used (via the ``uv.lock`` file) to help with safer updates and additions to the environment, and to ensure reproducibility.

  .. group-tab:: conda

    1. (If you do not have conda already) Install Miniconda: https://docs.conda.io/en/latest/miniconda.html

    2. Set the conda-forge channel as the priority to install packages from::

        conda config --add channels conda-forge
        conda config --set channel_priority strict

    You should do this to avoid mixing packages from the anaconda channel (which can result in broken environments), and try to get all packages from conda-forge where available for consistency.

    3. Create a new environment with some packages (including viresclient)::

        conda create --name myenv python=3.12 jupyterlab scipy matplotlib cartopy viresclient

    4. Activate the new environment (you do this each time you want to use it)::

        conda activate myenv

    5. Or run a command directly from within the environment (without needing to activate it), e.g.::

        conda run -n myenv jupyter lab

  .. group-tab:: mamba

    1. Download and install `Miniforge <https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html>`_

    2. Create a new environment with some packages (including viresclient)::

        mamba create --name myenv python=3.12 jupyterlab scipy matplotlib cartopy viresclient

    3. Activate the new environment (you do this each time you want to use it)::

        mamba activate myenv

    4. Or run a command directly from within the environment (without needing to activate it), e.g.::

        mamba run -n myenv jupyter lab


  .. group-tab:: docker

    viresclient is available in several publicly available (experimental) Docker images:

    - `Swarm DISC SwarmPAL processor (swarmpal-processor) <https://github.com/Swarm-DISC/SwarmPAL-processor/pkgs/container/swarmpal-processor>`_
    - `Python in Heliophysics Community environment (pyhc-environment) <https://hub.docker.com/r/spolson/pyhc-environment>`_

  .. group-tab:: cloud / online

    Online services provide access to a range of scientific software within a Jupyter environment. viresclient may be pre-installed or can be added as above.

    - `ESA Swarm VRE <https://vre.vires.services/>`_

      - Run by us in connection with VirES (free self-signup, included with your VirES account)
    - `ESA Datalabs <https://datalabs.esa.int/>`_

      - Requires an authorised ESA Cosmos account
    - `HelioCloud <https://heliocloud.org/>`_

      - In development

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
