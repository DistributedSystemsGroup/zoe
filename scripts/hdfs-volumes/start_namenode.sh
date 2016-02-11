#!/bin/bash

NETWORK_NAME=hdfs
NETWORK_ID=eeef9754c16790a29d5210c5d9ad8e66614ee8a6229b6dc6f779019d46cec792

VOLUME_PATH=/mnt/hdfs/namenode

SWARM=192.168.45.252:2380

IMAGE=192.168.45.252:5000/zoerepo/hadoop-namenode

docker -H $SWARM run -i -t -d --name hdfs-namenode \
                              -h hdfs-namenode \
                              -e NAMENODE_HOST=hdfs-namenode \
                              -e constraint:node==bf12 \
                              -m 2g \
                              -v $VOLUME_PATH:/mnt/namenode \
                              --net $NETWORK_NAME \
                              $IMAGE

