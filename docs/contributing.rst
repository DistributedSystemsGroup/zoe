.. _contributing:

Contributing to Zoe
===================

Zoe is an open source and project: we welcome any kind of contribution to the code base, the documentation, on the general architecture. Bug reports and features requests are also accepted and treasured.

To better work together we have established some rules on how to contribute.

Bug reports and feature requests
--------------------------------

Bug reports and feature requests are handled through the GitHub issue system at: `https://github.com/DistributedSystemsGroup/zoe/issues <https://github.com/DistributedSystemsGroup/zoe/issues>`_

The issue system should be used for only for bug reports or feature requests. If you have more general questions, you need help setting up Zoe or running some application, please use the mailing list.

The mailing list
----------------

The first step is to subscribe to the mailing list: `http://www.freelists.org/list/zoe <http://www.freelists.org/list/zoe>`_

Use the mailing list to stay up-to-date with what other developers are working on, to discuss and propose your ideas. We prefer small and incremental contributions, so it is important to keep in touch with the rest of the community to receive feedback. This way your contribution will be much more easily accepted.

Code and documentation contributions
------------------------------------

To contribute code and/or documentation you should follow this workflow:

1. announce your idea on the mailing list, to prevent duplicated work
2. fork the Zoe repository via GitHub (if you don't already have a fork)
3. create a branch that will hold your changes
4. ... develop and debug ...
5. when you are ready propose your changes on the mailing list

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

Contributors can setup their own CI pipeline following the quality guidelines (:ref:`quality`). At a bare minimum all code should be tested via the `run_tests.sh` script available in the root of the repository. Accepted contributions will be run through the CI pipeline at Eurecom before being published on the public repository.
