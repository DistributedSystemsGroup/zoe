.. _developer_documentation:

Developer documentation
=======================

As a developer you can:

- call Zoe from your own software: :ref:`Zoe REST API documentation <rest-api>`
- create ot modify ZApps: :ref:`howto_zapp`
- contribute to Zoe: keep reading

Contributing to Zoe
-------------------

Zoe is open source and all kinds of contributions are welcome.

Zoe is licensed under the terms of the Apache 2.0 license.

Bugs, issues and feature requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Zoe issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_

Testing beta code
^^^^^^^^^^^^^^^^^

The ``HEAD`` of the master branch represents the latest version of Zoe. Automatic tests are performed before code is merged into master, but human feedback is invaluable. Clone the repository and report on the `mailing list <http://www.freelists.org/list/zoe>`_ or on the `issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.

Code changes and pull requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**When you contribute code, you affirm that the contribution is your original work and that you license the work to the project under the project’s open source license. Whether or not you state this explicitly, by submitting any copyrighted material via pull request, email, or other means you agree to license the material under the project’s open source license and warrant that you have the legal authority to do so.**

To contribute code and/or documentation you should follow this workflow:

1. announce your idea on the mailing list, to prevent duplicated work
2. fork the Zoe repository via GitHub (if you don't already have a fork)
3. ... develop and debug ...
4. when you are ready propose your changes with a pull request

Zoe maintainers will review your code, give constructive feedback and eventually accept the code and merge.

Contributors can setup their own CI pipeline following the quality guidelines (:ref:`quality`). At a bare minimum all code should be tested via the `run_tests.sh` script available in the root of the repository. Accepted contributions will be run through the full Zoe CI pipeline before being merged in the public repository.

Repository contents
^^^^^^^^^^^^^^^^^^^

- `docs`: Sphinx documentation used to build these pages
- `scripts`: scripts for deployment and testing
- `zoe_api`: the front-end Zoe process that provides the REST API
- `zoe_cmd`: Command-line client
- `zoe_lib`: library, contains common modules needed by the api and the master processes
- `zoe_master`: the back-end Zoe process schedules and talks to the containerization system
- `contrib`: supervisord config files and sample ZApps


Internal module/class/method documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
  :maxdepth: 1

  auth
  rest-api
  api-endpoint
  master-api
  scheduler
  backend
  stats
  jenkins-ci
  gitlab-ci
  integration_test

:ref:`modindex`
