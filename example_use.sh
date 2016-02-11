#!/usr/bin/env bash

P3=`which python3`

$P3 ./zoe.py user-new venzano@eurecom.fr
$P3 ./zoe.py app-new --user-id 1 tests/resources/spark-notebook-test.json
$P3 ./zoe.py start 1

