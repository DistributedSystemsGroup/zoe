#!/bin/sh

SPARK_VER=1.4.1
HADOOP_VER=hadoop2.4

python ./gen_dockerfiles.py $SPARK_VER $HADOOP_VER

for d in master worker shell submit notebook; do
  cd $d
  docker build -t 10.0.0.2:5000/venza/spark-$d:$SPARK_VER .
  docker push 10.0.0.2:5000/venza/spark-$d:$SPARK_VER
  cd ..
  docker -H 10.0.0.2:2380 pull 10.0.0.2:5000/venza/spark-$d:$SPARK_VER
done
