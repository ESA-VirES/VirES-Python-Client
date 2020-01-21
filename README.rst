
.. image:: https://badge.fury.io/py/viresclient.svg
    :target: https://badge.fury.io/py/viresclient

.. image:: https://readthedocs.org/projects/viresclient/badge/?version=latest
    :target: http://viresclient.readthedocs.io/
    :alt: Documentation Status

.. image:: https://requires.io/github/ESA-VirES/VirES-Python-Client/requirements.svg?branch=master
    :target: https://requires.io/github/ESA-VirES/VirES-Python-Client/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://travis-ci.org/ESA-VirES/VirES-Python-Client.svg?branch=master
    :target: https://travis-ci.org/ESA-VirES/VirES-Python-Client

.. image:: https://coveralls.io/repos/github/ESA-VirES/VirES-Python-Client/badge.svg
    :target: https://coveralls.io/github/ESA-VirES/VirES-Python-Client

.. image:: https://zenodo.org/badge/138034133.svg
   :target: https://zenodo.org/badge/latestdoi/138034133

::

  pip install viresclient

viresclient_ is a Python package which connects to a VirES_ server through the WPS_ interface and handles product requests and downloads. This enables easy access to ESA's `Swarm mission`_ data and models. This service is provided for ESA by EOX_. For enquiries or help, please email info@vires.services or `raise an issue on GitHub`_.

.. _viresclient: https://github.com/ESA-VirES/VirES-Python-Client
.. _VirES: https://vires.services
.. _WPS: http://www.opengeospatial.org/standards/wps
.. _`Swarm mission`: https://earth.esa.int/web/guest/missions/esa-operational-eo-missions/swarm
.. _EOX: https://eox.at/category/vires/
.. _`raise an issue on GitHub`: https://github.com/ESA-VirES/VirES-Python-Client/issues

Data and models are processed on demand on the server - a combination of measurements from any time interval can be accessed. These are the same data that can be accessed by the `VirES GUI`_. *viresclient* handles the returned data to allow direct loading as a single pandas.DataFrame_, or xarray.Dataset_.

.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe
.. _xarray.Dataset: http://xarray.pydata.org/en/stable/data-structures.html#dataset
.. _`VirES GUI`: https://vires.services

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


*viresclient* is installed on the `"Virtual Research Environment" (VRE)`_, which is a managed Jupyter-based system provided for ESA by EOX. The service is free and open to all.

.. _`"Virtual Research Environment" (VRE)`: https://vre.vires.services/

.. image:: https://github.com/ESA-VirES/Swarm-VRE/raw/master/docs/images/VRE_shortest_demo.gif


How to acknowledge VirES
------------------------

You can reference *viresclient* directly using the DOI of our zenodo_ record. VirES uses data from a number of different sources so please also acknowledge these appropriately.

.. _zenodo: https://doi.org/10.5281/zenodo.2554162
