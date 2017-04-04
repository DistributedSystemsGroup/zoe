.. _quality:

Testing and quality assurance
=============================

Every commit that hits the master branch on the public repository of Zoe has to pass a testing gate.

All contributions to the codebase are centralised into an internal repository at Eurecom. There, every commit (on any branch) triggers a continuous integration pipeline that verifies code quality and runs tests. Only commits and merges on the master branch for which the Jenkins build succeeds are pushed to the public repository.

GitHub has been configured to protect the master branch on the `Zoe repository <https://github.com/DistributedSystemsGroup/zoe>`_. It will accept only pushes that are marked with a status check. This, together with Jenkins pushing only successful builds, guarantees that the quality of the published code respects our standards.

The CI pipeline in detail
-------------------------

Different contributors use different software for managing the CI pipeline.

* :ref:`ci-jenkins`
* :ref:`ci-gitlab`

SonarQube
^^^^^^^^^

`SonarQube <https://www.sonarqube.org/>`_  is a code quality tool that performs a large number of static tests on the codebase. It applies rules from well-known coding standards like Misra, Cert and CWE and generates a quality report.

We configured our test pipeline to fail if the code quality of new commits is below the following rules:

* Coverage less than 80%
* Maintainability worse than A
* Reliability worse than A
* Security rating worse than A


Documentation
^^^^^^^^^^^^^

Sphinx documentation is tested with the ``doc8`` tool with default options.

Integration tests
^^^^^^^^^^^^^^^^^

Refer to the :ref:`integration-test` documentation for details.

Zapp image vulnerability scan
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We use **clair**, a vulnerability static analyzer for Containers, from **CoreOS** to analyze Zoe docker image before using it.

If the base image you are using to build Zoe has too many vulnerabilities, you could choose another images which have less vulnerabilities.

The result after analyzing would be on the **console output** of the Jenkins job for Zoe. Insert the script below into the Zoe's Jenkins job to do the Clair analysis, all the necessary files could be found on ``ci/clair`` folder::

  export imageID=`docker image inspect <your-registry-address>/zoe:$BUILD_ID | grep "Id" | awk -F ' ' '{print $2}' | awk -F ',' '{print $1}' | awk -F '"' '{print $2}'`
  docker exec clair_clair analyzer $imageID


RAML API description
--------------------

Under the directory ``contrib/raml`` there is the `RAML <http://raml.org/>`_ description of the Zoe API.
