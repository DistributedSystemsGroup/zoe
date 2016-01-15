#!/bin/bash

set -e

pushd ../utils
. base.sh
popd

NAMENODE_IMAGE=$REGISTRY/zoerepo/hadoop-namenode
DATANODE_IMAGE=$REGISTRY/zoerepo/hadoop-datanode

DATANODE_COUNT=3

if [ -f state.zoe ]; then
    echo "Error a cluster is already running"
    exit 1
fi

PFX=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 3 | head -n 1`

echo -n "Starting HDFS NameNode container..."
NN_ID=`$DOCKER run --name namenode-$PFX -h namenode-$PFX -e NAMENODE_HOST=namenode-$PFX -d $NAMENODE_IMAGE`
echo "done"
echo $NN_ID > state.zoe

NN_IP=`$DOCKER inspect --format '{{ .NetworkSettings.IPAddress }}' $NN_ID`
echo "NameNode is at $NN_IP:8020, web interface at http://$NN_IP:50070"

echo -n "Starting DataNode(s)... "
for w in `seq $DATANODE_COUNT`; do
    DN_ID=`$DOCKER run --name datanode-$PFX-$w -h datanode-$PFX-$w -e NAMENODE_HOST=namenode-$PFX -d $DATANODE_IMAGE`
    echo -n "$w "
    echo $DN_ID >> state.zoe
done
echo done

echo "Creating nbuser home directory on HDFS"
$DOCKER exec -it $NN_ID /opt/hadoop/bin/hdfs dfs -mkdir /user
$DOCKER exec -it $NN_ID /opt/hadoop/bin/hdfs dfs -mkdir /user/nbuser
$DOCKER exec -it $NN_ID /opt/hadoop/bin/hdfs dfs -chown nbuser:users /user/nbuser

