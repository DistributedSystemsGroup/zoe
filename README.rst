Zoe - Container-based Analytics as a Service
============================================

Zoe provides a simple way to provision data analytics applications using containers.

Resources:

- Main website: http://zoe-analytics.eu
- Documentation: http://docs.zoe-analytics.eu
- How to install: http://docs.zoe-analytics.eu/en/latest/install.html
- Project roadmap and guidelines: https://github.com/DistributedSystemsGroup/zoe/wiki

Zoe applications can be easily created by users, we provide several examples in the `zoe-applications https://github.com/DistributedSystemsGroup/zoe-applications`_ repository to get you started.

Other Zoe resources:

- Zoe applications: https://github.com/DistributedSystemsGroup/zoe-applications
- Development and API documentation: http://docs.zoe-analytics.eu/en/latest/developer/index.html


A note on releases and the master branch
----------------------------------------
The Zoe master branch is tested before being published and only commits that pass the tests are published on this repository. A description of the CI pipeline is here: http://docs.zoe-analytics.eu/en/latest/quality.html

Official releases are tagged with their version number in the repository and changes for each released version are summarised in the `ChangeLog https://github.com/DistributedSystemsGroup/zoe/blob/master/CHANGELOG.md`_ file.

Repository contents
-------------------

- `contrib`: supervisord config files
- `docs`: Sphinx documentation
- `scripts`: Scripts used to test Zoe images outside of Zoe
- `zoe_cmd`: Command-line client
- `zoe_lib`: Client-side library, contains also some modules needed by the observer and the master processes
- `zoe_master`: The core of Zoe, the server process that listens for client requests and creates the containers on Swarm
- `zoe_api`: The web client interface

|Documentation Status|

Zoe is licensed under the terms of the Apache 2.0 license.

.. |Documentation Status| image:: https://readthedocs.org/projects/zoe-analytics/badge/?version=latest
   :target: https://readthedocs.org/projects/zoe-analytics/?badge=latest
