Configuration Details
=====================

While it is possible to enter the server URL and access credentials (see :doc:`access_token`) each time a new request object is created,

.. code-block:: python

  from viresclient import SwarmRequest

  # both URL and access token passed as request object's parameters
  request = SwarmRequest(
      url="https://vires.services/ows",
      token="r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-"
  )

it is more convenient to omit them from the code and store them in a private configuration file. This configuration can be done using the :meth:`viresclient.set_token` convenience function, the underlying :meth:`viresclient.ClientConfig` module, or the command line interface (CLI) - see below. These will all set the configuration options in a file which is by default located at ``~/.viresclient.ini`` which can be edited directly, containing for example::

  [https://vires.services/ows]
  token = r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

  [default]
  url = https://vires.services/ows

When creating the configuration file manually make sure the file is readable by its owner only::

    $ chmod 0600 ~/.viresclient.ini
    $ ls -l ~/.viresclient.ini
    -rw-------  1 owner owner  361 May 12 09:12 /home/owner/.viresclient.ini

When the configuration file is present, then the url and token options can be omitted from requests:

.. code-block:: python

  # access token read from configuration
  request = SwarmRequest(url="https://vires.services/ows")

  # both default URL and access token read from configuration
  request = SwarmRequest()

The following sections describe how to set the configuration.


Configuration via CLI
^^^^^^^^^^^^^^^^^^^^^

The ``viresclient`` shell command can be used to set the server access configuration::

  $ viresclient set_token https://vires.services/ows
  Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

  $ viresclient set_default_server https://vires.services/ows

See also: :doc:`cli`

Configuration via Python
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code to store the token in the ``viresclient`` configuration:

.. code-block:: python

  from viresclient import ClientConfig

  cc = ClientConfig()
  cc.set_site_config("https://vires.services/ows", token="r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-")
  cc.default_url = "https://vires.services/ows"
  cc.save()

Alternatively, use the convenience function:

.. code-block:: python

  from viresclient import set_token
  set_token("https://vires.services/ows")
  # (you will now be prompted to enter the token)

which calls the same code as above, but makes sure the token remains hidden so that it can't accidentally be shared.


For developers & DISC users
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The accounts for the staging server (``staging.vires.services``), and DISC server (``staging.viresdisc.vires.services``) are separate. Tokens can be similarly generated on these and stored in the same configuration file alongside the others::

  $ viresclient set_token https://staging.vires.services/ows
  Enter access token: r-8-mlkP_RBx4mDv0di5Bzt3UZ52NGg-

  $ viresclient set_token https://staging.viresdisc.vires.services/ows
  Enter access token: VymMHhWjZ-9nSVs-FuPC27ca8C6cOyij

Using ``SwarmRequest()`` without the ``url`` parameter will use the default URL set above. To access a non-default server the URL parameter must be used:

.. code-block:: python

  from viresclient import SwarmRequest

  # request using the default server (https://vires.services/ows)
  request = SwarmRequest()

  # request to an alternative, non-default server
  request = SwarmRequest(url="https://staging.viresdisc.vires.services/ows")

The older HTTP basic access authentication (i.e. username + password) is still available on the DICS staging server and these credentials can also be configured::

  $ viresclient set_password https://staging.viresdisc.vires.services/openows
  Enter username [jovyan]: <username>
  Enter password: ***********

However, this interface is deprecated and it will be removed in future and it is recommended to switch to the token-based authentication.
