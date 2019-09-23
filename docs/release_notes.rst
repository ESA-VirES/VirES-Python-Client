Release notes
=============

Changes from 0.4.1 to 0.4.2
---------------------------

- Fixed orbit number queries (get_orbit_number)
- Added model sources to model info

Changes from 0.4.0 to 0.4.1
---------------------------

- Added low level data upload API and CLI
- Added set_token convenience function for quick configuration
- Changed list of accessible models:

  - Removed ``MCO_SHA_2F``, ``SIFM``
  - Added ``MF7``, ``LCS-1``

Changes from 0.3.0 to 0.4.0
---------------------------

- Fixed issues with running on Windows
- Enforcing Python v3.5+ for installation
- Allowing higher versions of cdflib, pandas, and xarray
- Added CLI configuration for setting server address and token
- Metadata for source lineage is now easier to access (names of original ESA data files, details of models used, and filters applied). These are set as properties of :meth:`viresclient.ReturnedData` (i.e. ``data``) and as metadata (``.attrs``) in the ``Dataset`` returned from ``.as_xarray()``::

    data.sources
    data.magnetic_models
    data.range_filters

    ds = data.as_xarray()
    ds.Sources
    ds.MagneticModels
    ds.RangeFilters

- Added access to collections ``SW_OPER_IPDxIRR_2F``
- Added auxiliary data ``F107`` which is the hourly F10.7 value. This is in addition to ``F10_INDEX`` which was already present, which is a daily average.
- Added possibility of accessing multiple collections simultaneously, e.g.::

    request.set_collection("SW_OPER_MAGA_LR_1B", "SW_OPER_MAGC_LR_1B")

- Added optional "expansion" of dataframes with::

    data.as_dataframe(expand=True)

  This expands columns which contain vectors (e.g. ``B_NEC``) into separate columns named like: ``B_NEC_N``, ``B_NEC_E``, ``B_NEC_C``. This is recommended so that numpy operations will work on the columns. The default is ``expand=False`` to preserve the older behaviour.

Changes from v0.2.6 to 0.3.0
----------------------------

- Service officially open to public through self-registration on https://vires.services
- Token-based authentication added

Changes from v0.2.5 to 0.2.6
----------------------------

- New model composition behaviour is implemented, extending what is possible with the ``models`` kwarg in :meth:`viresclient.SwarmRequest.set_products` (with backwards compatibility). See demo in https://github.com/smithara/viresclient_examples/blob/master/model_residuals_and_cartopy.ipynb
- New method :meth:`viresclient.SwarmRequest.get_model_info` to fetch model details from server.
- :meth:`viresclient.SwarmRequest.available_models` is updated with these details.
- New parameters in TEC collections: ``Elevation_Angle``, ``Absolute_VTEC``.
- New parameters in auxiliaries: ``OrbitDirection``, ``QDOrbitDirection``.
- The auxiliary ``Kp`` is now provided as the proper Kp value, and ``Kp10`` is provided with the old behaviour with the value of Kp*10.
- Updated dependency on cdflib to v0.3.9, and xarray to allow both v0.10.x and v0.11.x.

Changes from v0.2.4 to 0.2.5
----------------------------

- EFI collections have changed from ``SW_OPER_EFIx_PL_1B`` to ``SW_OPER_EFIx_LP_1B``, with different measurement variables
- Added support for user-defined models by providing a .shc file path as the ``custom_model`` in :meth:`viresclient.SwarmRequest.set_products`. Model evaluations and residuals will then be returned, named as "Custom_Model", in the same way as other models behave.
- Added alternative input start and end times as ISO-8601 strings to :meth:`viresclient.SwarmRequest.get_between`
- Minor bug fixes

Changes from v0.2.1 to v0.2.4
-----------------------------

- Added models CHAOS-6-MMA-Primary and CHAOS-6-MMA-Secondary

Changes from v0.2.0 to v0.2.1
-----------------------------

 - Improved performance of pandas and xarray loading from cdf.
 - Added ``nrecords_limit`` option to :meth:`viresclient.SwarmRequest.get_between` to override the default maximum number of records in each request. Use this if a request is failing with a server error that the maximum allowable number of records has been exceeded - but this means that there is probably duplicate data on the server (old and new versions), so check the data that gets returned::

    data = request.get_between(start_time, end_time, nrecords_limit=3456000)
    ds = data.as_xarray()
    # Identify negative time jumps
    np.where(np.diff(ds["Timestamp"]).astype(float) < 0)
    # e.g [2519945, 5284745, 5481414]
    for i in [2519945, 5284745, 5481414]:
        print(ds.isel(Timestamp=i))
    # Length of day should be 86400
    ds.sel(Timestamp='2014-02-02')

 - Added ``tmpdir`` option to :meth:`viresclient.SwarmRequest.get_between` to override the default temporary file directory. The default is selected automatically according to https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp (usually /tmp). This may not be suitable when fetching large amounts of data as some machines may have limited space available in /tmp or there may be a higher performance or preferred location.

Changes from v0.1.0 to v0.2.0
-----------------------------

 - Now use ``SwarmRequest`` instead of ``ClientRequest``.
 - kwarg ``subsample`` changed to ``sampling_step``.
 - Added references to .available_collections() and .available_models().
 - User credentials are automatically stored in a configuration file ``~/.viresclient.ini``.
 - Downloads are streamed to temporary files instead of being held in memory.
 - Any size request is now supported. Large requests are automatically chunked up.
 - Added download progress bar indicating size in MB.
 - xarray added as a dependency and ``.as_xarray()`` method added.
