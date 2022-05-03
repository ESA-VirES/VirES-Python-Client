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

Remove stored configuration::

  $ viresclient clear_credentials

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
    is valid:      True
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

or::

  $ viresclient show_uploads https://staging.vires.services/ows
  eff3bd47-0098-45d3-ba9e-158bea0fae12
    filename:      test_incomplete.cdf
    is valid:      False
    data start:    2019-02-02T23:59:59Z
    data end:      2019-02-03T23:59:58Z
    uploaded on:   2019-09-11T08:04:58.055294Z
    content type:  application/x-cdf
    size:          959888
    MD5 checksum:  778cfe6e60568b08750187dfc917b3e8
    missing mandatory fields:
      Latitude
      Longitude
    constant fields:
      Radius=6371200.0
    fields:
      B_NEC
      F
      Radius
      Timestamp

Note the :code:`is valid: False` flag, missing mandatory fields :code:`Latitude`
and :code:`Longitude`, and extra constant field :code:`Radius`.

Remove any uploaded file::

  $ viresclient clear_uploads <url>

e.g.::

  $ viresclient clear_uploads https://vires.services/ows
  69f91765-ce9f-4be3-8475-76f7e0eb1d92[test.csv] removed


Setting extra constant parameters::

  $ viresclient set_upload_parameters https://staging.vires.services/ows -p "Latitude=43.78" -p "Longitude=12.34"
  eff3bd47-0098-45d3-ba9e-158bea0fae12: parameters updated

  $ viresclient show_uploads https://staging.vires.services/ows
  eff3bd47-0098-45d3-ba9e-158bea0fae12
    filename:      test_incomplete.cdf
    is valid:      True
    data start:    2019-02-02T23:59:59Z
    data end:      2019-02-03T23:59:58Z
    uploaded on:   2019-09-11T08:04:58.055294Z
    content type:  application/x-cdf
    size:          959888
    MD5 checksum:  778cfe6e60568b08750187dfc917b3e8
    constant fields:
      Latitude=43.78
      Longitude=12.34
      Radius=6371200.0
    fields:
      B_NEC
      F
      Latitude
      Longitude
      Radius
      Timestamp

Removing constant parameters::

  $ viresclient clear_upload_parameters https://staging.vires.services/ows
  eff3bd47-0098-45d3-ba9e-158bea0fae12: parameters removed

  $ viresclient show_uploads https://staging.vires.services/ows
  eff3bd47-0098-45d3-ba9e-158bea0fae12
    filename:      test_tt2000.cdf
    is valid:      False
    data start:    2019-02-02T23:59:59Z
    data end:      2019-02-03T23:59:58Z
    uploaded on:   2019-09-11T08:04:58.055294Z
    content type:  application/x-cdf
    size:          959888
    MD5 checksum:  778cfe6e60568b08750187dfc917b3e8
    missing mandatory fields:
      Latitude
      Longitude
    fields:
      B_NEC
      F
      Timestamp
