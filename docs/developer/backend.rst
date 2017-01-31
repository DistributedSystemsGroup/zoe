.. _devel_backend:

Backend abstraction
===================

The container backend Zoe uses is configurable at runtime. Internally there is an API that Zoe, in particular the scheduler, uses to communicate with the container backend. This document explains the API, so that new backends can be created and maintained.

Zoe assumes backends are composed of multiple nodes. In case the backend is not clustered or does not expose per-node information, it can be implemented in Zoe as exposing a single node.

Package structure
-----------------

Backends are written in Python and live in the ``zoe_master/backends/`` directory. Inside there is one Python package for each backend implementation.

To let Zoe use a new backend, its class must be imported in ``zoe_master/backends/interface.py`` and the ``_get_backend()`` function should be modified accordingly. Then the choices in ``zoe_lib/config.py`` for the configuration file should be expanded to include the new backend name.

More options to the configuration file can be added to support the new backend. Use the ``--<backend name>-<option name>`` convention for them.

API
---

Whenever Zoe needs to access the container backend it will create a new instance of the backend class. The class must be a child of ``zoe_master.backends.base.BaseBackend``.

.. autoclass:: zoe_master.backends.base.BaseBackend
   :members:
