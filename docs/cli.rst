Command Line Interface (CLI)
============================

Get list of the available CLI commands::

  $ viresclient --help

Get help on a specific CLI command::

  $ viresclient <command> --help


1. Configuration
----------------

Set default server::

  $ viresclient set_default_server <url>

Remove default server::

  $ viresclient remove_default_server <url>

Set access token configuration (aka site configuration)::

  $ viresclient set_token <url>
  Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

Remove site configuration configuration::

  $ viresclient set_token remove_server <url>

Show current configuration::

  $ viresclient show_configuration
  ...

2. Data Upload
--------------

Upload CDF or CSV data files to VirES for Swarm server::

  $ viresclient upload_file <url> <filename>

e.g.::

  $ viresclient upload_file https://vires.services/ows ./test.csv
  69f91765-ce9f-4be3-8475-76f7e0eb1d92[test.csv] uploaded


Show information about the currently uploaded file::

  $ viresclient show_uploads <url>

e.g.::

  $ viresclient show_uploads https://vires.services/ows
  69f91765-ce9f-4be3-8475-76f7e0eb1d92
    filename:      test.csv
    data start:    2016-01-01T00:30:00Z
    data end:      2016-01-01T04:30:00Z
    uploaded on:   2019-09-04T08:50:30.592982Z
    content type:  text/csv
    size:          421
    MD5 checksum:  8afe55c47385d1556117e81bf5ba8c34
    fields:
      B_C
      B_E
      B_N
      B_NEC
      Latitude
      Longitude
      Observatory
      Radius
      Timestamp

Remove any uploaded file::

  $ viresclient clear_uploads <url>

e.g.::

  $ viresclient clear_uploads https://vires.services/ows
  69f91765-ce9f-4be3-8475-76f7e0eb1d92[test.csv] removed
