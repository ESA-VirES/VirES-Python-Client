.. image:: https://img.shields.io/pypi/pyversions/viresclient
   :target: https://pypi.org/project/viresclient/
   :alt: Python Version

.. image:: https://img.shields.io/pypi/v/viresclient
   :target: https://pypi.org/project/viresclient/
   :alt: PyPI

.. image:: https://img.shields.io/conda/vn/conda-forge/viresclient
   :target: https://anaconda.org/conda-forge/viresclient
   :alt: Conda

.. image:: https://readthedocs.org/projects/viresclient/badge/?version=latest
    :target: http://viresclient.readthedocs.io/
    :alt: Documentation Status

.. image:: https://zenodo.org/badge/138034133.svg
   :target: https://zenodo.org/badge/latestdoi/138034133

``viresclient`` is a Python package which provides access to products (including on-demand processing) from two of ESA's Earth Explorer missions: `Swarm`_ and `Aeolus`_. This service is provided for ESA by EOX_. For enquiries about the service and problems with accessing your account, please email info@vires.services. For help with usage, please email ashley.smith@ed.ac.uk or `raise an issue on GitHub`_.

.. _WPS: http://www.opengeospatial.org/standards/wps
.. _Swarm: https://earth.esa.int/eogateway/missions/swarm
.. _Aeolus: https://earth.esa.int/eogateway/missions/aeolus
.. _EOX: https://eox.at/tag/vires/
.. _`raise an issue on GitHub`: https://github.com/ESA-VirES/VirES-Python-Client/issues

There are two VirES services (Virtual environments for Earth Scientists) which *viresclient* can communicate with:

- *VirES for Swarm:*

  - Interact with the `VirES for Swarm graphical interface (web client) <https://vires.services>`_
  - Browse code recipes: `Swarm Notebooks <https://notebooks.vires.services>`_
  - JupyterHub: `Swarm VRE (Virtual Research Environment) <https://vre.vires.services>`_
  - Swarm data documentation: `Swarm handbook <https://swarmhandbook.earth.esa.int>`_
  - *Note that this service is not only for Swarm*:

    - Multi-mission products including magnetometry from CHAMP, CryoSat-2, and more
    - INTERMAGNET ground magnetometers via the ``AUX_OBS`` collection
    - Custom geomagnetic model evaluation

  - Read more about the ecosystem: `Python tools for ESA's Swarm mission: VirES for Swarm and surrounding ecosystem <https://doi.org/10.3389/fspas.2022.1002697>`_

- *VirES for Aeolus:*

  - Interact with the `VirES for Aeolus graphical interface (web client) <https://aeolus.services>`_
  - Browse code recipes: `Aeolus Notebooks <https://notebooks.aeolus.services>`_
  - JupterHub: `Aeolus VRE <https://vre.aeolus.services>`_
  - `Aeolus data documentation <https://earth.esa.int/eogateway/missions/aeolus/data>`_

Data and models are processed on demand on the VirES server - a combination of measurements from any time interval can be accessed. These are the same data that can be accessed by the VirES GUI. *viresclient* handles the returned data to allow direct loading as a single pandas.DataFrame_, or xarray.Dataset_.

.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe
.. _xarray.Dataset: http://xarray.pydata.org/en/stable/data-structures.html#dataset

.. code-block:: python

 from viresclient import SwarmRequest

 # Set up connection with server
 request = SwarmRequest()
 # Set collection to use
 # - See https://viresclient.readthedocs.io/en/latest/available_parameters.html
 request.set_collection("SW_OPER_MAGA_LR_1B")
 # Set mix of products to fetch:
 #  measurements (variables from the given collection)
 #  models (magnetic model predictions at spacecraft sampling points)
 #  auxiliaries (variables available with any collection)
 # Optionally set a sampling rate different from the original data
 request.set_products(
     measurements=["F", "B_NEC"],
     models=["CHAOS-Core"],
     auxiliaries=["QDLat", "QDLon"],
     sampling_step="PT10S"
 )
 # Fetch data from a given time interval
 # - Specify times as ISO-8601 strings or Python datetime
 data = request.get_between(
     start_time="2014-01-01T00:00",
     end_time="2014-01-01T01:00"
 )
 # Load the data as an xarray.Dataset
 ds = data.as_xarray()

::

 <xarray.Dataset>
 Dimensions:           (NEC: 3, Timestamp: 360)
 Coordinates:
 * Timestamp         (Timestamp) datetime64[ns] 2014-01-01 ... 2014-01-01T00:59:50
 Dimensions without coordinates: NEC
 Data variables:
   Spacecraft        (Timestamp) <U1 'A' 'A' 'A' 'A' 'A' ... 'A' 'A' 'A' 'A'
   Latitude          (Timestamp) float64 -1.229 -1.863 -2.496 ... 48.14 48.77
   Longitude         (Timestamp) float64 -14.12 -14.13 -14.15 ... 153.6 153.6
   Radius            (Timestamp) float64 6.878e+06 6.878e+06 ... 6.868e+06
   F                 (Timestamp) float64 2.287e+04 2.281e+04 ... 4.021e+04
   F_CHAOS-Core      (Timestamp) float64 2.287e+04 2.282e+04 ... 4.02e+04
   B_NEC             (Timestamp, NEC) float64 2.01e+04 -4.126e+03 ... 3.558e+04
   B_NEC_CHAOS-Core  (Timestamp, NEC) float64 2.011e+04 ... 3.557e+04
   QDLat             (Timestamp) float64 -11.99 -12.6 -13.2 ... 41.59 42.25
   QDLon             (Timestamp) float64 58.02 57.86 57.71 ... -135.9 -136.0
 Attributes:
   Sources:         ['SW_OPER_MAGA_LR_1B_20140101T000000_20140101T235959_050...
   MagneticModels:  ["CHAOS-Core = 'CHAOS-Core'(max_degree=20,min_degree=1)"]
   RangeFilters:    []




.. image:: https://github.com/ESA-VirES/Swarm-VRE/raw/master/docs/images/VRE_shortest_demo.gif


How to acknowledge VirES
------------------------

You can reference *viresclient* directly using the DOI of our zenodo_ record. VirES uses data from a number of different sources so please also acknowledge these appropriately.

.. _zenodo: https://doi.org/10.5281/zenodo.2554162

    | "We use the Python package, viresclient [1], to access [...] from ESA's VirES for Swarm service [2]"
    | [1] https://doi.org/10.5281/zenodo.2554162
    | [2] https://vires.services

You can also cite this paper:

   | Smith A.R.A., Pačes M. and Swarm DISC (2022) Python tools for ESA’s Swarm mission: VirES for Swarm and surrounding ecosystem. Front. Astron. Space Sci. 9:1002697. doi: 10.3389/fspas.2022.1002697
