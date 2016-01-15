#!/bin/bash

set -e

pushd ../utils
. base.sh
popd

MASTER_IMAGE=$REGISTRY/zoerepo/spark-master
WORKER_IMAGE=$REGISTRY/zoerepo/spark-worker
NOTEBOOK_IMAGE=$REGISTRY/zoerepo/spark-jupyter-notebook

WORKER_COUNT=3
WORKER_RAM=7g
CONTAINER_RAM=8g
WORKER_CORES=4

EXECUTOR_RAM=6g

if [ -f state.zoe ]; then
    echo "Error a cluster is already running"
    exit 1
fi

echo -n "Starting Spark master container..."
MASTER_ID=`$DOCKER run -d -p 8080:8080 $MASTER_IMAGE`
echo "done"
echo $MASTER_ID > state.zoe

MASTER_IP=`$DOCKER inspect --format '{{ .NetworkSettings.IPAddress }}' $MASTER_ID`
echo "Spark master is at http://$MASTER_IP:8080"

echo -n "Starting workers... "
for w in `seq $WORKER_COUNT`; do
    WORKER_ID=`$DOCKER run -e SPARK_MASTER_IP=$MASTER_IP -e SPARK_WORKER_RAM=$WORKER_RAM -e SPARK_WORKER_CORES=$WORKER_CORES -m $CONTAINER_RAM -d $WORKER_IMAGE`
    echo -n "$w "
    echo $WORKER_ID >> state.zoe
done
echo done

echo -n "Starting notebook..."
NB_ID=`$DOCKER run -e SPARK_MASTER=spark://$MASTER_IP:7077 -e SPARK_EXECUTOR_RAM=$EXECUTOR_RAM -p 8888:8888 -p 4040:4040 -d $NOTEBOOK_IMAGE`
echo "done"
echo $NB_ID >> state.zoe

NB_IP=`$DOCKER inspect --format '{{ .NetworkSettings.IPAddress }}' $NB_ID`
echo "iPython notebook is available at http://$NB_IP:8888"

