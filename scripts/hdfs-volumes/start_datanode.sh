#!/bin/bash

NETWORK_NAME=hdfs
NETWORK_ID=eeef9754c16790a29d5210c5d9ad8e66614ee8a6229b6dc6f779019d46cec792

VOLUME=/mnt/hdfs/datanode

SWARM=192.168.45.252:2380

IMAGE=192.168.45.252:5000/zoerepo/hadoop-datanode

#NODES="bf12 bf13 bf14 bf15"
NODES="bf15"

for node in $NODES; do

docker -H $SWARM run -i -t -d --name hdfs-datanode-$node \
                              -h hdfs-datanode-$node \
                              -e NAMENODE_HOST=hdfs-namenode \
                              -e constraint:node==$node \
                              -m 1g \
                              --net $NETWORK_NAME \
                              -v $VOLUME:/mnt/datanode \
                               $IMAGE

done

