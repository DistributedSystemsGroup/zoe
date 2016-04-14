Zoe - Container-based Analytics as a Service
============================================

Zoe provides a simple way to provision data analytics applications using Docker Swarm.

Resources:

-  Main website: http://zoe-analytics.eu
-  Documentation: http://docs.zoe-analytics.eu
-  How to install: http://zoe-analytics.readthedocs.org/en/latest/install.html

Zoe applications can be easily created by users, we provide several examples in the `zoe-applications https://github.com/DistributedSystemsGroup/zoe-applications`_ repository to get you started.

Repository contents
-------------------

- `contrib`: supervisord config files
- `docs`: Sphinx documentation
- `scripts`: Scripts used to test Zoe images outside of Zoe
- `zoe_cmd`: Command-line client
- `zoe_lib`: Client-side library, contains also some modules needed by the observer and the master processes
- `zoe_logger`: Optional Kafka producer for Docker container logs
- `zoe_observer`: The Observer process that monitors Swarm and informs the master of various events
- `zoe_master`: The core of Zoe, the server process that listens for client requests and creates the containers on Swarm
- `zoe_web`: The web client interface

|Travis build| |Documentation Status| |Requirements Status|

Zoe is licensed under the terms of the Apache 2.0 license.

.. |Documentation Status| image:: https://readthedocs.org/projects/zoe-analytics/badge/?version=latest
   :target: https://readthedocs.org/projects/zoe-analytics/?badge=latest
.. |Requirements Status| image:: https://requires.io/github/DistributedSystemsGroup/zoe/requirements.svg?branch=master
   :target: https://requires.io/github/DistributedSystemsGroup/zoe/requirements/?branch=master
   :alt: Requirements Status
.. |Travis build| image:: https://travis-ci.org/DistributedSystemsGroup/zoe.svg
   :target: https://travis-ci.org/DistributedSystemsGroup/zoe
