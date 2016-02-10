Zoe - Container-based Analytics as a Service
============================================

Zoe provides a simple way to provision data analytics applications using Docker Swarm.

Resources:

-  Main website: http://zoe-analytics.eu
-  Documentation: http://docs.zoe-analytics.eu
-  How to install: http://zoe-analytics.readthedocs.org/en/latest/install.html

Zoe can use any Docker image, but we provide some for the pre-configured applications available in the client (Spark and HDFS):

-  Docker images: https://github.com/DistributedSystemsGroup/zoe-docker-images

Repository contents
-------------------

- `contrib`: supervisord config files
- `docs`: Sphinx documentation
- `scripts`: Scripts used to test Zoe images outside of Zoe
- `zoe_cmd`: Command-line client
- `zoe_lib`: Client-side library, contains also some modules needed by the observer and the scheduler processes
- `zoe_observer`: The Observer process that monitors Swarm and informs the scheduler of various events
- `zoe_scheduler`: The core of Zoe, the server process that listens for client requests and creates the containers on Swarm
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