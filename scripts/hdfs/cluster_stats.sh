#!/bin/bash

pushd ../utils
. base.sh
popd

$DOCKER stats `cat state.zoe`

