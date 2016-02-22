#!/usr/bin/env bash

for i in `seq -w 1 50`; do ./zoe.py user-new --name group$i --pass group$i --role guest; done

./zoe.py pre-app-export spark_jupyter_notebook_lab > /tmp/zoeapp.json

for i in `seq -w 1 50`; do
    export ZOE_USER=group$i
    export ZOE_PASS=group$i
    ./zoe.py app-new /tmp/zoeapp.json
done

for i in `seq -w 1 50`; do
    export ZOE_USER=group$i
    export ZOE_PASS=group$i
    ./zoe.py start spark-jupyter-lab lab-session
done

