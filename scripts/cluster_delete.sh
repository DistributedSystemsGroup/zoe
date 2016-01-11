#!/bin/bash

set -e

. utils/base.sh

for id in `cat state.zoe`; do
	echo -n "Deleting container "
	docker -H $SWARM rm -f $id
done

rm state.zoe

