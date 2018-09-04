Release notes
=============

Changes from v0.2.0 to v0.2.1
-----------------------------

 - Improved performance of pandas and xarray loading from cdf.
 - Added option to override the default nrecords_limit (maximum number of records in each request). Use this if a request is failing with a server error that the maximum allowable number of records has been exceeded - but this means that there is probably duplicate data on the server (old and new versions), so check the data that gets returned::

    data = request.get_between(start_time, end_time, nrecords_limit=3456000)
    ds = data.as_xarray()
    # Identify negative time jumps
    np.where(np.diff(ds["Timestamp"]).astype(float) < 0)
    # e.g [2519945, 5284745, 5481414]
    for i in [2519945, 5284745, 5481414]:
        print(ds.isel(Timestamp=i))
    # Length of day should be 86400
    ds.sel(Timestamp='2014-02-02')

 - Added option to override the default temporary file directory.

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
