.. _ci-gitlab:

Zoe Continuous Integration with Gitlab pipelines
================================================

Overview
--------

GitLab offers an `integrated way of running a CI pipeline <https://docs.gitlab.com/ce/ci/README.html>`_ via the GitLab runners system. The Zoe repository contains the pipeline description in the ``.gitlab-ci.yml`` file.

To use it, we suggest to configure the GitLab runner (`documentation <https://docs.gitlab.com/runner/>`_) with the Docker executor. This ensures tests are run in a clean and isolated environment.

Runner configuration
--------------------

Using the Docker executor, we configured our runner with these options::

    concurrent = 5
    check_interval = 0

    [[runners]]
      name = "ci-server"
      url = "https://gitlab.eurecom.fr/ci"
      token = "<your-token-here>"
      executor = "docker"
      [runners.docker]
        image = "docker:latest"
        disable_cache = false
        volumes = ["/cache", "/tls/certificates/ca.crt:/registry-ca.crt:ro", "/var/run/docker.sock:/var/run/docker.sock"]
      [runners.cache]
        Insecure = false

Please note that since our private registry is protected with TLS, we need to pass also the CA certificate to be able to push Docker images build inside the CI pipeline.

Variables
---------

To run the tests a number of variables need to be set from the GitLab interface:

* DOCKER_REGISTRY: the URL of the registry
* REGISTRY_PASSWORD: the password used for authenticating with the registry via docker login
* SONARQUBE_SERVER_URL: the URL of the SonarQube server
* SONARQUBE_USER: the SonarQube user
* SSH_PRIVATE_KEY: private key to be used to deploy via rsync the staging build
* STAGING_IP: IP/hostname of the staging server
* WEB_STAGING_PATH: path for the web interface on the staging server
* ZOE_STAGING_PATH: path for Zoe on the staging server
* SWARM_URL: URL of a docker engine/swarm to run integration tests

SonarQube
---------

To run SonarQube against Zoe we use a special Docker image, `available on the Docker Hub <https://hub.docker.com/r/zoerepo/sonar-scanner/>`_.

You can also build it from the Dockerfile available at ``ci/gitlab-sonar-scanner/``, relative to the repository root.
