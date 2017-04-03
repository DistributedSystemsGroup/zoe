.. _integration-test:

Zoe Integration Tests
=====================

* Overview

  - Testing the zoe rest api in action.
  - The backend could be swarm or kubernetes

* What will it do

  - Launch two containers for zoe-api and zoe-master, one for postgresql
  - Connect to the backend (kubernetes/swarm) and test the rest API of zoe.
  - The authentication type is ``text`` for simplicity.
  - The test would be described in a Jenkins job
  - The whole process could be described in below steps:
  - Build the container image for zoe. The tag is the $BUILD_ID from jenkins
  - Deploy zoe with the new image, base on the docker-compose-test.yml
  - Start the test for all api
  - Generate coverage report
  - Push the built image to the private registry
  - Deploy zoe with the new image, base on the docker-compose-prod.yml

The job stops whenever one of the step above fails.

The last two steps could be optional if there’s no need to deploy zoe everytime.

* How to do it

  - Requirements:

    - A workable cluster. It could be Kubernetes or Swarm
    - A private registry to push the built images.
    - The runner for the integration test is contained in zoeci.py file
    - Arguments explanation:

      - argv[1]: 0: deploy, 1: build, 2: push
      - args[2]: address for docker sock
      - For build case:
          - args[3]: private_registry_address/zoe:$BUILD_ID
      - For deploy case:
          - args[3]: docker-compose file location
          - args[4]: private_registry_address/zoe:$BUILD_ID

  - Explanation on script for Jenkins job can be found on the document of continuous integration of Zoe.

* How to expand it?

  - The initial infrastructure could be reused.
  - Current tests of zoe use the unittest built-in library of Python, new library could be used based on the need.
  - Current tests of zoe focus on testing the behaviors of the rest api:

    - info
    - userinfo
    - execution
    - service
  - with two types of authentication:

    - text
    - cookie
  - and two scenarios:

    - success
    - failure

  - The new tests could be added into ``tests`` folder
