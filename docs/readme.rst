Introduction
============

This is the documentation for the ``viresclient`` Python package. This is a tool which connects to a VirES_ server through the WPS_ interface and handles product requests and downloads. This enables easy access to ESA's Swarm mission data and models. For enquiries or help, please email info@vires.services or `raise an issue on GitHub`_

.. _VirES: https://vires.services
.. _WPS: http://www.opengeospatial.org/standards/wps
.. _`raise an issue on GitHub`: https://github.com/ESA-VirES/VirES-Python-Client/issues

Some links where you can read more about VirES:

 - `VirES web service`_
 - `Swarm DQW slides about viresclient`_
 - `EOX blog posts`_
 - `Swarm mission`_

 .. _`VirES web service`: https://vires.services/
 .. _`Swarm DQW slides about viresclient`: https://github.com/smithara/viresclient_examples/blob/master/viresclient_SwarmDQW8.pdf
 .. _`EOX blog posts`: https://eox.at/category/vires/
 .. _`Swarm mission`: https://earth.esa.int/web/guest/missions/esa-operational-eo-missions/swarm

Data can be accessed from the server as CSV or CDF files and saved to disk, or loaded directly into Python objects pandas.DataFrame_, or xarray.Dataset_.

.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe

.. _xarray.Dataset: http://xarray.pydata.org/en/stable/data-structures.html#dataset

cdflib_ is used to read CDF files.

.. _cdflib: https://github.com/MAVENSDC/cdflib

The project is on GitHub at https://github.com/ESA-VirES/VirES-Python-Client - please feel free to contribute with any code/suggestions/comments.

A repository of example notebooks can be found at https://github.com/smithara/viresclient_examples. We welcome contribution of notebooks to this repository that show some short analyses or generating useful figures.

How to acknowledge VirES
------------------------

You can reference ``viresclient`` directly using the DOI of our zenodo_ record. VirES uses data from a number of different sources so please also acknowledge these appropriately.

 .. _zenodo: https://doi.org/10.5281/zenodo.2554163
