#!/usr/bin/env bash

ZOE_TEST_IMAGE=${ZOE_TEST_IMAGE:-zoe:manual}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-docker-registry:5000}

docker build --pull -t ${DOCKER_REGISTRY}/ci/${ZOE_TEST_IMAGE} .
docker push ${DOCKER_REGISTRY}/ci/${ZOE_TEST_IMAGE}
