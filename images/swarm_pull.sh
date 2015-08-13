#!/bin/sh

SPARK_VER=1.4.1

for d in master worker shell submit notebook; do
  docker -H 10.0.0.2:2380 pull 10.0.0.2:5000/venza/spark-${d}:${SPARK_VER}
done
