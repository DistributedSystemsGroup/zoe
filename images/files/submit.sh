#!/usr/bin/env bash
cd /opt/spark/
./bin/spark-submit --master spark://${SPARK_MASTER_IP}:7077 --executor-memory=${SPARK_EXECUTOR_RAM} "$@" 
