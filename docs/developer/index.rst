.. _developer_documentation:

Developer documentation
=======================

Repository contents
-------------------

- `contrib`: supervisord config files
- `docs`: Sphinx documentation
- `scripts`: Scripts used to test Zoe images outside of Zoe
- `zoe_cmd`: Command-line client
- `zoe_lib`: Client-side library, contains also some modules needed by the observer and the master processes
- `zoe_master`: The core of Zoe, the server process that listens for client requests and creates the containers on Swarm
- `zoe_api`: The web client interface

:ref:`modindex`

.. toctree::
  :maxdepth: 2

  introduction
  rest-api
  auth
  api-endpoint
  master-api
  scheduler
  backend
  stats
