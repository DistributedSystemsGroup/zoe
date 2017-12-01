.. _integration-test:

Zoe Integration Tests
=====================

Overview
--------

The objective of integration testing is to run Zoe through a simple workflow to test basic functionality in an automated manner.

How it works
------------

The integration tests are sun by GitLab CI, but can also be run by hand. Docker is used to guarantee reproducibility and a clean environment for each test run.

Two containers are used:

* Standard Postgres 9.3
* Python 3.4 container with the Zoe code under test

Pytest will start a zoe-api and a zoe-master, then proceed querying the REST API via HTTP calls.

* The DockerEngine back-end is used
* The authentication type is ``text`` for simplicity.

The code is under the ``integration_tests`` directory.

What is being tested
--------------------

The following endpoints are tested, with good and bad authentication information. Return status codes are checked for correctness.

* info
* userinfo
* execution start, list, terminate
* service list

A simple ZApp with an nginx web server is used for testing the execution start API.
