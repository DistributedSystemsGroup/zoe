#!/usr/bin/env bash

docker build -f Dockerfile.test -t zoe_test_image .

docker network create zoe_test

docker run -d --network zoe_test --name postgres -p 5432:5432 -e POSTGRES_DB=zoe -e POSTGRES_USER=zoeuser -e POSTGRES_PASSWORD=zoepass postgres:9.3
docker pull nginx:alpine
sleep 4  # give postgres the time to start
docker run -it --network zoe_test --name zoe zoe_test_image pytest --tb=short --cov-report=term --cov zoe_api --cov zoe_lib --cov zoe_master tests/basic_auth_success_test.py

docker rm -f zoe postgres
docker network rm zoe_test
