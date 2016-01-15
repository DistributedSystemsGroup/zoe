#!/bin/bash

pushd utils
source base.sh
popd

$DOCKER ps -a

