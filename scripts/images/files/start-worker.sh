#!/usr/bin/env bash
cd /opt/spark
export SPARK_LOCAL_IP=`awk 'NR==1 {print $1}' /etc/hosts`
./bin/spark-class org.apache.spark.deploy.worker.Worker \
	spark://${SPARK_MASTER_IP}:7077 --cores ${SPARK_WORKER_CORES:-4} --memory ${SPARK_WORKER_RAM:-4g} \
	-h ${SPARK_LOCAL_IP} \
	"$@"
