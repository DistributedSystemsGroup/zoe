#!/bin/sh

SWARM_MANAGER=10.0.0.2:2380
REGISTRY=10.0.0.2:5000
MASTER_IMAGE=$REGISTRY/venza/spark-master:1.4.1
WORKER_IMAGE=$REGISTRY/venza/spark-worker:1.4.1
SHELL_IMAGE=$REGISTRY/venza/spark-shell:1.4.1
SUBMIT_IMAGE=$REGISTRY/venza/spark-submit:1.4.1

WORKER_COUNT=3
WORKER_RAM=8g
WORKER_CORES=4

MASTER_ID=`docker -H $SWARM_MANAGER run -d $MASTER_IMAGE`

MASTER_IP=`docker -H $SWARM_MANAGER inspect --format '{{ .NetworkSettings.IPAddress }}' $MASTER_ID`

echo "Spark master is at $MASTER_IP"

for w in `seq $WORKER_COUNT`; do
	docker -H $SWARM_MANAGER run -e SPARK_MASTER_IP=$MASTER_IP -e SPARK_WORKER_RAM=$WORKER_RAM -e SPARK_WORKER_CORES=$WORKER_CORES -d $WORKER_IMAGE
done

if [ "$1" == "--shell" ]; then
	docker -H $SWARM_MANAGER run -i -t -e SPARK_MASTER_IP=$MASTER_IP -e SPARK_EXECUTOR_RAM=$WORKER_RAM $SHELL_IMAGE
fi

if [ "$1" == "--submit" ]; then
	docker -H $SWARM_MANAGER run --rm -i -t -e SPARK_MASTER_IP=$MASTER_IP -e SPARK_EXECUTOR_RAM=$WORKER_RAM -v /mnt/cephfs/temp/spark-apps:/apps $SUBMIT_IMAGE /opt/submit.sh /apps/wordcount.py hdfs://192.168.45.157/datasets/gutenberg_big_2x.txt hdfs://192.168.45.157/tmp/cntwdc1
fi
