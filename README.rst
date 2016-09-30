Zoe - Container-based Analytics as a Service
============================================

Zoe provides a simple way to provision data analytics applications using Docker Swarm.

Resources:

-  Main website: http://zoe-analytics.eu
-  Documentation: http://docs.zoe-analytics.eu
-  How to install: http://zoe-analytics.readthedocs.org/en/latest/install.html

Zoe applications can be easily created by users, we provide several examples in the `zoe-applications https://github.com/DistributedSystemsGroup/zoe-applications`_ repository to get you started.

Other Zoe resources:

- Zoe applications: https://github.com/DistributedSystemsGroup/zoe-applications
- Zoe logger: https://github.com/DistributedSystemsGroup/zoe-logger


A note on the master branch
---------------------------
We are currently redesigning Zoe with a new architecture, so the master branch is unstable and changes very rapidly.
The latest stable version is maintained under the 0.9.7-stable branch. All the documentation currently refers to this stable version, unless otherwise noted.


Repository contents
-------------------

- `contrib`: supervisord config files
- `docs`: Sphinx documentation
- `scripts`: Scripts used to test Zoe images outside of Zoe
- `zoe_cmd`: Command-line client
- `zoe_lib`: Client-side library, contains also some modules needed by the observer and the master processes
- `zoe_master`: The core of Zoe, the server process that listens for client requests and creates the containers on Swarm
- `zoe_api`: The web client interface

|Travis build| |Documentation Status|

Zoe is licensed under the terms of the Apache 2.0 license.

.. |Documentation Status| image:: https://readthedocs.org/projects/zoe-analytics/badge/?version=latest
   :target: https://readthedocs.org/projects/zoe-analytics/?badge=latest
.. |Travis build| image:: https://travis-ci.org/DistributedSystemsGroup/zoe.svg
   :target: https://travis-ci.org/DistributedSystemsGroup/zoe
