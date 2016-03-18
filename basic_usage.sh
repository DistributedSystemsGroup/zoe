#!/usr/bin/env bash

set -e

export ZOE_USER=admin
export ZOE_PASS=changeme
export ZOE_URL=http://localhost:4850

echo "Get statistics"
./zoe.py stats
echo "Get superuser"
./zoe.py user-get zoeadmin
echo "Create a new user"
./zoe.py user-new --name test --password test --role guest
echo "Delete a user"
./zoe.py user-rm test
echo "Export an application template"
./zoe.py pre-app-export hdfs > /tmp/zoe-hdfs.json
