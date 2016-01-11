#!/bin/bash

set -e

. utils/base.sh

MASTER_IMAGE=$REGISTRY/zoerepo/spark-master
WORKER_IMAGE=$REGISTRY/zoerepo/spark-worker
NOTEBOOK_IMAGE=$REGISTRY/zoerepo/spark-ipython-notebook

echo $MASTER_IMAGE

WORKER_COUNT=3
WORKER_RAM=7g
CONTAINER_RAM=8g
WORKER_CORES=4

EXECUTOR_RAM=6g

SPARK_SHELL_OPTIONS=""

if [ -f state.zoe ]; then
    echo "Error a cluster is already running"
    exit 1
fi

echo -n "Starting Spark master container..."
MASTER_ID=`docker -H $SWARM run -d $MASTER_IMAGE`
echo "done"
echo $MASTER_ID > state.zoe

MASTER_IP=`docker -H $SWARM inspect --format '{{ .NetworkSettings.IPAddress }}' $MASTER_ID`
echo "Spark master is at http://$MASTER_IP:8080"

echo -n "Starting workers... "
for w in `seq $WORKER_COUNT`; do
    WORKER_ID=`docker -H $SWARM run -e SPARK_MASTER_IP=$MASTER_IP -e SPARK_WORKER_RAM=$WORKER_RAM -e SPARK_WORKER_CORES=$WORKER_CORES -m $CONTAINER_RAM -d $WORKER_IMAGE`
    echo -n "$w "
    echo $WORKER_ID >> state.zoe
done
echo done

echo -n "Starting notebook..."
NB_ID=`docker -H $SWARM run -e SPARK_MASTER_IP=$MASTER_IP -e SPARK_EXECUTOR_RAM=$EXECUTOR_RAM -e SPARK_OPTIONS=$SPARK_SHELL_OPTIONS -d $NOTEBOOK_IMAGE`
echo "done"
echo $NB_ID >> state.zoe

NB_IP=`docker -H $SWARM inspect --format '{{ .NetworkSettings.IPAddress }}' $NB_ID`
echo "iPython notebook is available at http://$NB_IP:8888"

