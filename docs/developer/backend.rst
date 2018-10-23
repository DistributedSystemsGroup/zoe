.. _devel_backend:

Back-end abstraction
====================

The container back-end Zoe uses is configurable at runtime. Internally there is an API that Zoe, in particular the scheduler, uses to communicate with the container back-end. This document explains the API, so that new back-ends can be created and maintained.

Zoe assumes back-ends are composed of multiple nodes. In case the back-end is not clustered or does not expose per-node information, it can be implemented in Zoe as exposing a single big node. In this case, however, many of the smart scheduling features of Zoe will be unavailable.

Package structure
-----------------

Back-ends are written in Python and live in the ``zoe_master/backends/`` directory. Inside there is one Python package for each backend implementation.

To let Zoe use a new back-end, its class must be imported in ``zoe_master/backends/interface.py`` and the ``_get_backend()`` function should be modified accordingly. Then the choices in ``zoe_lib/config.py`` for the configuration file should be expanded to include the new back-end class name.

More options to the configuration file can be added to support the new backend. Use the ``--<backend name>-<option name>`` convention for them. If the new options do not fit the zoe.conf format, a separate configuration file can be used, like in the DockerEngine and Kubernetes cases.

API
---

Whenever Zoe needs to access the container back-end it will create a new instance of the back-end class. The class must be a child of ``zoe_master.backends.base.BaseBackend``. The class is not used as a singleton and may be instantiated concurrently, multiple times and in different threads.

.. autoclass:: zoe_master.backends.base.BaseBackend
   :members:
