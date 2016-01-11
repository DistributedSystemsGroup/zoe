#!/bin/bash

. utils/base.sh

docker -H $SWARM stats `cat state.zoe`

