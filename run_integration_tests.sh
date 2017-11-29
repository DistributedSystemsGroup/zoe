#!/usr/bin/env bash

if [ -z ${CI_PIPELINE_ID} ]; then
    docker build -f Dockerfile.test -t zoe_test_image .

    docker network create zoe_test

    docker run -d --network zoe_test --name postgres -p 5432:5432 -e POSTGRES_DB=zoe -e POSTGRES_USER=zoeuser -e POSTGRES_PASSWORD=zoepass postgres:9.3
    docker pull nginx:alpine
    sleep 4  # give postgres the time to start
    docker run -it --network zoe_test --name zoe zoe_test_image pytest integration_tests/

    docker rm -f zoe postgres
    docker network rm zoe_test
else  # running in CI
    pytest --tb=short integration_tests/
fi
