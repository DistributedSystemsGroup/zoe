#!/usr/bin/env bash

ZOE_TEST_IMAGE=${ZOE_TEST_IMAGE:-zoe:manual}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-docker-registry:5000}
CI_BUILD_REF=${CI_BUILD_REF:-manual}

if [ z${CI_BUILD_REF} != z"manual" ]; then
    echo "Start Postgres"
    docker run --name postgres-${CI_BUILD_REF} -d -p 5432 postgres:9.3
    sleep 5
fi

echo "Start Zoe API process"
python3 zoe-api.py --debug --backend-swarm-url http://localhost:2375 --deployment-name test${CI_BUILD_REF} --dbuser postgres --dbhost localhost --dbport 5432 --dbname postgres --dbpass postgres --master-url tcp://localhost:4850 --auth-type text --proxy-type none --listen-port 5100 --workspace-base-path /tmp --log-file /tmp/zoe-api-${CI_BUILD_REF}.log &

echo "Start Zoe Master process"
python3 zoe-master.py --debug --backend-swarm-url http://172.17.0.1:2375 --deployment-name test${CI_BUILD_REF} --dbuser postgres --dbhost postgres-${CI_BUILD_REF} --dbport 5432 --dbname postgres --dbpass postgres --auth-type text --proxy-type none --workspace-base-path /tmp --log-file /tmp/zoe-master-${CI_BUILD_REF}.log &

cd tests
coverage run basic_auth_success_test.py localhost:5100

cd ..

echo "<============== MASTER LOGS ======================>"
cat /tmp/zoe-master-${CI_BUILD_REF}.log

echo "<================ API LOGS =======================>"
cat /tmp/zoe-api-${CI_BUILD_REF}.log


if [ z${CI_BUILD_REF} != z"manual" ]; then
    echo "Stop Postgres"
    docker rm -f postgres-${CI_BUILD_REF}
fi
