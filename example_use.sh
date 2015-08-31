#!/usr/bin/env bash

P3=`which python3`

$P3 ./zoectl.py user-new venzano@eurecom.fr
$P3 ./zoectl.py spark-notebook-new --user-id 1 --name "small notebook" --worker-count 2 --executor-memory 2g --executor-cores 2
$P3 ./zoectl.py spark-app-new --user-id 1 --name "wordcount medium" --worker-count 8 --executor-memory 8g --executor-cores 8 --file ../wordcount.zip
