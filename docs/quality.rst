.. _quality:

Testing and quality assurance
=============================

Every commit that hits the master branch on the public repository of Zoe has to pass a testing gate.

All contributions to the codebase are centralised into an internal repository at Eurecom. There, every commit (on any branch) triggers a continuous integration pipeline that verifies code quality and runs tests. Only commits and merges on the master branch for which the Jenkins build succeeds are pushed to the public repository.

GitHub has been configured to protect the master branch on the `Zoe repository <https://github.com/DistributedSystemsGroup/zoe>`_. It will accept only pushes that are marked with a status check. This, together with Jenkins pushing only successful builds, guarantees that the quality of the published code respects our standards.

A description of the CI pipeline is available in the :ref:`ci-gitlab` page.

Sphinx documentation is tested with the ``doc8`` tool with default options.

Refer to the :ref:`integration-test` documentation for details on integration testing.
