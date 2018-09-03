Release notes
=============

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
