.. _quality:

Testing and quality assurance
=============================

Every commit that hits the master branch on the public repository of Zoe has to pass a testing gate.

All contributions to the codebase are centralised into an internal repository at Eurecom. There, every commit (on any branch) triggers a continuous integration pipeline that verifies code quality and runs tests. Only commits and merges on the master branch for which the Jenkins build succeeds are pushed to the public repository.

GitHub has been configured to protect the master branch on the `Zoe repository <https://github.com/DistributedSystemsGroup/zoe>`_. It will accept only pushes that are marked with a status check. This, together with Jenkins pushing only successful builds, guarantees that the quality of the published code respects our standards.

The CI pipeline in detail
-------------------------

Jenkins is triggered via a hook script on the internal Eurecom repository.

SonarQube
^^^^^^^^^

`SonarQube <https://www.sonarqube.org/>`_  is a code quality tool that performs a large number of static tests on the codebase. It applies rules from well-known coding standards like Misra, Cert and CWE.

SonarQube provides a feature that aggregates static test results into simple measures of overall code quality.

We configured the Jenkins build to fail if the code quality of new commits is below the following rules:

* Coverage less than 80%
* Maintainability worse than B
* Reliability worse than B
* Security rating worse than A

We plan to move to A rating for all measures after some clean ups and refactoring on the code.

Documentation
^^^^^^^^^^^^^

Sphinx documentation is tested with the ``doc8`` tool with default options.

Integration tests
^^^^^^^^^^^^^^^^^

Zoe is composed of two main processes and depends on a number of external services. In this setting, creating and maintaining credible mock-ups for unit testing would slow down the development too much.

Instead we are working on a suite of integration tests that will run Zoe components against real, live instances of the services Zoe depends on.

These tests will also be run before commits are pushed to the public repository.
