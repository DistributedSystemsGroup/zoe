#!/usr/bin/env bash

cd /opt/spark-notebook

cat ../application.conf | sed -e "s/SPARK_MASTER_IP/$SPARK_MASTER_IP/" -e "s/SPARK_EXEC_RAM/$SPARK_EXECUTOR_RAM/" > conf/application.conf

./bin/spark-notebook -Dconfig.file=./conf/application.conf -Dapplication.context=/proxy/$PROXY_ID
