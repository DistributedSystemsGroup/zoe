#!/usr/bin/env bash
export SPARK_MASTER_IP=`awk 'NR==1 {print $1}' /etc/hosts`
export SPARK_LOCAL_IP=`awk 'NR==1 {print $1}' /etc/hosts`
export SPARK_MASTER_PORT=7077
export SPARK_MASTER_WEBUI_PORT=8080

cd /opt/spark
./bin/spark-class org.apache.spark.deploy.master.Master \
  --host $SPARK_MASTER_IP --port $SPARK_MASTER_PORT --webui-port $SPARK_MASTER_WEBUI_PORT \
  $@

