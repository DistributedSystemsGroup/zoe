#!/bin/sh

SPARK_VER=1.4.1
IMAGE_VER=1.2

for d in master worker shell submit notebook; do
  docker -H 10.0.0.2:2380 pull 10.0.0.2:5000/zoe/spark-$d-${SPARK_VER}:${IMAGE_VER}
done
