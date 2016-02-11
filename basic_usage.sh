#!/usr/bin/env bash

set -e

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
echo "Upload the template as a new application"
./zoe.py app-new /tmp/zoe-hdfs.json
echo "Get the application back from Zoe"
./zoe.py app-get hdfs
echo "Delete the app"
./zoe.py app-rm hdfs
