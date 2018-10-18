    .. _contributing:

Contributing to Zoe
===================

Zoe is an open source and project: we welcome any kind of contribution to the code base, the documentation, on the general architecture. Bug reports and features requests are also accepted and treasured.

To better work together we have established some rules on how to contribute.

If you need ideas on features that are waiting to be implemented, you can check the `roadmap <https://github.com/DistributedSystemsGroup/zoe/wiki/RoadMap>`_.

Development repository
----------------------
Development happens at `Eurecom's GitLab repository <https://gitlab.eurecom.fr/zoe/main>`_. The GitHub repository is a read-only mirror.

The choice of GitLab over GitHub is due to the CI pipeline that we set-up to test Zoe. Please note the issue tracking for the Zoe project happens on GitHub.

Bug reports and feature requests
--------------------------------

Bug reports and feature requests are handled through the GitHub issue system at: `https://github.com/DistributedSystemsGroup/zoe/issues <https://github.com/DistributedSystemsGroup/zoe/issues>`_

Code and documentation contributions
------------------------------------

To contribute code and/or documentation you should follow this workflow:

1. check the issue tracker on GitHub to see if someone is already working on your idea
2. open a new issue stating your idea and how you wish to implement it
3. fork the Zoe repository via Eurecom's GitLab
4. create a branch that will hold your changes
5. ... develop and debug ...
6. when you are ready propose your changes on the mailing list

Zoe maintainers will review your code, give constructive feedback and eventually perform a pull and a merge.

Coding style
^^^^^^^^^^^^

Zoe code conforms to Python's `PEP8 coding style rules <https://www.python.org/dev/peps/pep-0008/>`_, with a few variations, detailed below:

* No line length limit
* All modules, classes, methods and functions must have a docstring
* The docstring for private methods is optional
* Names for unused variables and function parameters must end with ``_``

We also relaxed a number of pylint tests, check the ``.pylintrc`` file at the root of the source repository for details.

In general, if your code passes pylint, run with our configuration file with a 10/10 mark, it is ok and matches Zoe's coding rules.

Code quality and tests
^^^^^^^^^^^^^^^^^^^^^^

Before committing, all code should be tested via the `run_tests.sh` script available in the root of the repository.

All contributions to the codebase are centralised into a repository at Eurecom. There, every commit (on any branch) triggers a continuous integration pipeline that verifies code quality and runs tests. Only commits and merges on the master branch for which the CI succeeds are pushed to the public repository.

A description of the CI pipeline is available in the :ref:`ci-gitlab` page.

Sphinx documentation is tested with the ``doc8`` tool with default options.

Refer to the :ref:`integration-test` documentation for details on integration testing.
