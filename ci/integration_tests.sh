#!/usr/bin/env bash

CI_BUILD_REF=${CI_BUILD_REF:-manual}
ZOE_COMMON_OPTIONS="--debug --backend-swarm-url http://localhost:2375 --deployment-name test${CI_BUILD_REF} --dbuser postgres --dbhost localhost --dbport 5432 --dbname postgres --dbpass postgres --master-url tcp://localhost:4850 --auth-type text --proxy-type none --listen-port 5100 --workspace-base-path /tmp"

if [ z"${CI_BUILD_REF}" = z"manual" ]; then
    echo "Start Postgres"
    docker run --name postgres-${CI_BUILD_REF} -d -p 5432:5432 postgres:9.3
    sleep 5
fi

mkdir /tmp/test${CI_BUILD_REF}

python3 create_db_tables.py ${ZOE_COMMON_OPTIONS}

echo "Start Zoe API process"
python3 zoe-api.py ${ZOE_COMMON_OPTIONS} --log-file /tmp/zoe-api-${CI_BUILD_REF}.log &
API_PID=$!

sleep 2

echo "Start Zoe Master process"
python3 zoe-master.py ${ZOE_COMMON_OPTIONS} --log-file /tmp/zoe-master-${CI_BUILD_REF}.log &
MASTER_PID=$!

sleep 2

cd tests
coverage run basic_auth_success_test.py localhost:5100

cd ..

echo "<============== MASTER LOGS ======================>"
cat /tmp/zoe-master-${CI_BUILD_REF}.log
rm -f /tmp/zoe-master-${CI_BUILD_REF}.log

echo "<================ API LOGS =======================>"
cat /tmp/zoe-api-${CI_BUILD_REF}.log
rm -f /tmp/zoe-api-${CI_BUILD_REF}.log

kill ${API_PID} ${MASTER_PID}

rm -Rf /tmp/test${CI_BUILD_REF}

if [ z"${CI_BUILD_REF}" = z"manual" ]; then
    echo "Stop Postgres"
    docker rm -f postgres-${CI_BUILD_REF}
fi
